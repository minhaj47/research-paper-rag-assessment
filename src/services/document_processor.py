import fitz  # PyMuPDF
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
                "results and discussion",
                "findings",
                "analysis",
                "outcomes",
                "analysis",
                "findings",
            ],
            "conclusions": [
                "discussion and conclusions",
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
    # Helper: check if text appears in a context that suggests it's a header
    # -------------------------------------------------------------------------
    def _is_likely_header_context(self, text: str, font_size: float, median_size: float) -> bool:
        """Check if the text appears in a context that suggests it's a header"""
        
        # Very short text is more likely to be a header
        if len(text.split()) <= 3:
            return True
            
        # Text with numbering pattern is likely a header
        if self._header_re.match(text):
            return True
            
        # Larger font size suggests header
        if median_size > 0 and font_size >= median_size * 1.3:
            return True
            
        # Text that's all caps or title case might be a header
        words = text.split()
        if len(words) <= 6:
            # Check if most words are capitalized (title case)
            cap_ratio = sum(1 for word in words if word[0].isupper()) / len(words)
            if cap_ratio >= 0.8:
                return True
                
        # Text ending with colon often indicates a header
        if text.strip().endswith(':'):
            return True
            
        return False

    # -------------------------------------------------------------------------
    # Helper: detect headers
    # -------------------------------------------------------------------------
    def _detect_header(
        self, line_text: str, line_max_size: float, page_median_size: float
    ) -> Optional[str]:
        if not line_text:
            return None

        # Skip metadata lines
        lower = line_text.lower()
        if any(skip in lower for skip in self._skip_patterns):
            return None

        # Must be relatively short to be a header (not a paragraph)
        if len(line_text) > 150 or len(line_text.split()) > 20:
            return None

        # First check if this text appears in a header-like context
        if not self._is_likely_header_context(line_text, line_max_size, page_median_size):
            # If it doesn't look like a header context, be extra strict
            norm = self._strip_punct(line_text).lower()
            
            # Only allow exact matches for non-header-like contexts
            for canonical, variants in self.section_aliases.items():
                for variant in variants:
                    if norm == variant:
                        return canonical
            return None

        # Handle numbered headers (e.g., "2.1 Methods")
        match = self._header_re.match(line_text)
        if match:
            header_text = match.group("h").lower()
            norm = self._strip_punct(header_text)
            
            # For numbered headers, be more permissive
            for canonical, variants in self.section_aliases.items():
                for variant in variants:
                    if norm == variant or norm.startswith(variant):
                        return canonical
            return None

        # For potential headers in header-like context
        norm = self._strip_punct(line_text).lower()
        
        # Match exact or close variants
        for canonical, variants in self.section_aliases.items():
            for variant in variants:
                # Exact match
                if norm == variant:
                    return canonical
                # Starts with variant (e.g., "results and analysis")
                if norm.startswith(variant + " ") and len(norm.split()) <= len(variant.split()) + 3:
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
