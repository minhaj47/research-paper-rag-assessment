import pymupdf as fitz  # PyMuPDF
from typing import List, Dict, Any, Optional, Tuple
from io import BytesIO
import re
import string
import asyncio


class DocumentProcessor:
    def __init__(self, chunk_size: int = 1000, overlap: int = 200):
        self.chunk_size = chunk_size
        self.overlap = overlap

        # Canonical section name aliases for normalization
        self.section_aliases = {
            "abstract": ["abstract", "Abstract"],
            "introduction": ["introduction", "Introduction", "INTRODUCTION"],
            "methodology": [
                "methodology",
                "METHODOLOGY",
                "methods", 
                "materials and methods",
                "research methodology",
                "Research Methodology",
                "research methods",
                "experimental setup",
                "approach",
                "method",
            ],
            "results": [
                "Results",
                "findings",
                "analysis",
                "results and discussion",
                "outcomes",
                "discussion",
                "analysis and discussion",
                "findings and discussion",
            ],
            "conclusions": [
                "conclusions",
                "conclusion",
                "conclusion and future work",
                "summary",
                "concluding remarks",
                "future work",
            ],
            "references": [
                "references",
                "bibliography",
                "acknowledgment",
                "acknowledgement",
            ],
        }

        # Pre-compile regex patterns for better performance
        self._header_re = re.compile(r"^\s*(\d+(\.\d+)*)\.?\s*(?P<h>.+)$")
        self._whitespace_re = re.compile(r"\s+")
        
        # Pre-compile metadata skip patterns
        self._skip_patterns = {
            "doi", "http", "@", "received", "revised", "accepted", 
            "published", "license", "correspondence", "copyright"
        }

    # -------------------------------------------------------------------------
    # Public async entrypoint
    # -------------------------------------------------------------------------
    async def process_pdf(self, file_content: bytes) -> Dict[str, Any]:
        return await asyncio.to_thread(self._process_pdf_sync, file_content)

    # -------------------------------------------------------------------------
    # Core PDF logic
    # -------------------------------------------------------------------------
    def _process_pdf_sync(self, file_content: bytes) -> Dict[str, Any]:
        pdf_stream = BytesIO(file_content)
        doc = fitz.open(stream=pdf_stream, filetype="pdf")

        metadata = self._extract_metadata(doc)
        sections: Dict[str, Dict[str, Any]] = {"preamble": {"text": [], "start_page": 1}}
        current_section = "preamble"

        for page_index, page in enumerate(doc):
            page_no = page_index + 1
            blocks = page.get_text("dict").get("blocks", [])

            # Calculate median font size once per page
            sizes = [
                span.get("size", 0)
                for block in blocks
                for line in block.get("lines", [])
                for span in line.get("spans", [])
            ]
            page_median_size = self._median(sizes) if sizes else 0

            for block in blocks:
                if "lines" not in block:
                    continue
                    
                for line in block["lines"]:
                    spans = line.get("spans", [])
                    if not spans:
                        continue

                    text, max_size = self._merge_spans(spans)
                    text = text.strip()
                    if not text:
                        continue

                    # Detect header
                    header_token = self._detect_header(text, max_size, page_median_size)
                    if header_token:
                        current_section = header_token
                        if current_section not in sections:
                            sections[current_section] = {"text": [], "start_page": page_no}
                        sections[current_section]["text"].append(f"[PAGE {page_no}] {text}")
                        continue

                    # Front matter handling
                    if self._is_front_matter_line(text):
                        sections["preamble"]["text"].append(f"[PAGE {page_no}] {text}")
                        continue

                    # Regular content
                    if current_section not in sections:
                        sections[current_section] = {"text": [], "start_page": page_no}
                    sections[current_section]["text"].append(f"[PAGE {page_no}] {text}")

        doc.close()

        # Clean up empty sections and prepare output
        processed_sections: Dict[str, Any] = {}
        for name, content in sections.items():
            joined = " ".join(content["text"])
            if len(joined) <= 30:  # Skip tiny sections
                continue
                
            joined = self._whitespace_re.sub(" ", joined).strip()
            chunks = self._chunk_text(joined)

            processed_sections[name] = {
                "chunks": chunks,
                "chunk_count": len(chunks),
                "start_page": content.get("start_page", 1),
                "preview": joined[:250],
            }

        return {"metadata": metadata, "sections": processed_sections}

    # -------------------------------------------------------------------------
    # Helper: Merge text spans properly
    # -------------------------------------------------------------------------
    def _merge_spans(self, spans: List[Dict[str, Any]]) -> Tuple[str, float]:
        text = ""
        max_size = 0.0
        for span in spans:
            s_text = span.get("text", "").strip()
            size = span.get("size", 0)
            max_size = max(max_size, size)
    
            if not s_text:
                continue
    
            if text.endswith("-"):
                text = text[:-1] + s_text
            else:
                text += (" " if text else "") + s_text
        return text.strip(), max_size

    # -------------------------------------------------------------------------
    # Helper: detect headers
    # -------------------------------------------------------------------------
    def _detect_header(
        self, line_text: str, line_max_size: float, page_median_size: float
    ) -> Optional[str]:
        if not line_text:
            return None

        lower = line_text.lower()
        # Skip metadata lines
        if any(skip in lower for skip in self._skip_patterns):
            return None

        # Handle numbered headers (e.g., "2.1 Methods")
        match = self._header_re.match(line_text)
        norm = (match.group("h") if match else line_text).lower()
        norm = self._strip_punct(norm)

        # Check against known section patterns
        for canonical, variants in self.section_aliases.items():
            for variant in variants:
                if norm == variant or norm.startswith(variant + " ") or (variant in norm and len(norm) <= 80):
                    return canonical

        # Font-size heuristic for headers
        if (page_median_size and 
            line_max_size >= page_median_size * 1.25 and 
            len(norm) <= 80):
            for canonical, variants in self.section_aliases.items():
                for variant in variants:
                    if variant in norm:
                        return canonical

        return None

    # -------------------------------------------------------------------------
    # Helper: front-matter detection
    # -------------------------------------------------------------------------
    def _is_front_matter_line(self, text: str) -> bool:
        lower = text.lower()
        # Check for common metadata keywords
        front_matter_keywords = {
            "doi", "http", "license", "academic editor", "received", 
            "revised", "accepted", "published", "correspondence", "copyright", "basel"
        }
        if any(keyword in lower for keyword in front_matter_keywords):
            return True
            
        # Author-like lines (many commas or capitalized names)
        if text.count(",") >= 2 and len(text.split()) <= 8:
            words = text.split()
            cap_count = sum(1 for word in words if word[0].isupper() and len(word) > 1)
            return cap_count >= len(words) // 3
        return False

    # -------------------------------------------------------------------------
    # Metadata extraction
    # -------------------------------------------------------------------------
    def _extract_metadata(self, doc: fitz.Document) -> Dict[str, Any]:
        meta = doc.metadata or {}
        title = meta.get("title", "")
        author = meta.get("author", "")

        # Extract title from first page if not in metadata
        if not title:
            try:
                first_page = doc[0]
                candidates = []
                for block in first_page.get_text("dict").get("blocks", []):
                    for line in block.get("lines", []):
                        for span in line.get("spans", []):
                            text = span.get("text", "").strip()
                            size = span.get("size", 0)
                            if len(text) > 8:
                                candidates.append((size, text))
                
                # Sort by font size and find first valid title
                candidates.sort(key=lambda x: x[0], reverse=True)
                for _, txt in candidates:
                    if not any(skip in txt.lower() for skip in ["doi", "@"]) and txt.count(",") <= 2:
                        title = txt
                        break
            except Exception:
                pass

        return {
            "title": title or "Unknown",
            "author": author or "Unknown", 
            "page_count": doc.page_count,
        }

    # -------------------------------------------------------------------------
    # Chunking logic with overlap
    # -------------------------------------------------------------------------
    def _chunk_text(self, text: str) -> List[str]:
        sentences = re.split(r"(?<=[.!?])\s+", text)
        chunks = []
        current = ""
        
        for sentence in sentences:
            # If adding this sentence would exceed chunk size
            if len(current) + len(sentence) > self.chunk_size and current:
                chunks.append(current.strip())
                current = sentence
            else:
                current = f"{current} {sentence}".strip() if current else sentence
        
        if current:
            chunks.append(current.strip())

        # Simple overlap: add last N characters from previous chunk
        if self.overlap > 0 and len(chunks) > 1:
            for i in range(1, len(chunks)):
                prev_chunk = chunks[i-1]
                overlap_text = prev_chunk[-self.overlap:].lstrip()
                chunks[i] = f"{overlap_text} {chunks[i]}"

        return chunks

    # -------------------------------------------------------------------------
    # Utilities
    # -------------------------------------------------------------------------
    def _strip_punct(self, s: str) -> str:
        return s.translate(str.maketrans("", "", string.punctuation))

    def _median(self, arr: List[float]) -> float:
        if not arr:
            return 0.0
        arr = sorted(arr)
        n = len(arr)
        mid = n // 2
        return arr[mid] if n % 2 == 1 else (arr[mid - 1] + arr[mid]) / 2.0
