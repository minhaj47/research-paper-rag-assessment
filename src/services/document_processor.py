import pymupdf as fitz  # PyMuPDF
from typing import List, Dict, Any, Optional
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
            "abstract": ["abstract"],
            "introduction": ["introduction"],
            "methodology": [
                "methodology",
                "methods",
                "materials and methods",
                "Research methodology",
                "research methods",
                "experimental setup",
                "approach",
                "method",
            ],
            "results": [
                "results",
                "findings",
                "analysis",
                "results and discussion",
                "outcomes",
            ],
            "discussion": [
                "discussion",
                "analysis and discussion",
                "findings and discussion",
            ],
            "conclusion": [
                "conclusion",
                "conclusions",
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

        # Flatten list of all possible header phrases
        self.all_header_phrases = [
            h for variants in self.section_aliases.values() for h in variants
        ]

        # Detect numbered headers like "1. Introduction" or "2.1 Research Methodology"
        self._header_re = re.compile(r"^\s*(\d+(\.\d+)*)\.?\s*(?P<h>.+)$")

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

        sections: Dict[str, Dict[str, Any]] = {}
        current_section = "preamble"
        sections[current_section] = {"text": [], "start_page": 1}

        for page_index, page in enumerate(doc):
            page_no = page_index + 1
            blocks = page.get_text("dict").get("blocks", [])

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
                    if not text.strip():
                        continue

                    # Detect header
                    header_token = self._detect_header(text, max_size, page_median_size)
                    if header_token:
                        current_section = header_token
                        sections.setdefault(
                            current_section, {"text": [], "start_page": page_no}
                        )

                        # ✅ Keep full line (header + following text)
                        sections[current_section]["text"].append(f"[PAGE {page_no}] {text.strip()}")
                        continue

                    # Front matter handling
                    if self._is_front_matter_line(text):
                        sections.setdefault("preamble", {"text": [], "start_page": 1})
                        sections["preamble"]["text"].append(f"[PAGE {page_no}] {text.strip()}")
                        continue

                    # Regular content
                    sections.setdefault(current_section, {"text": [], "start_page": page_no})
                    sections[current_section]["text"].append(f"[PAGE {page_no}] {text.strip()}")

        doc.close()

        # Clean up tiny/empty sections
        sections = {
            k: v for k, v in sections.items() if len(" ".join(v.get("text", []))) > 30
        }

        # Chunk and prepare output
        processed_sections: Dict[str, Any] = {}
        for name, content in sections.items():
            joined = " ".join(content["text"]).strip()
            joined = re.sub(r"\s+", " ", joined)
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
    def _merge_spans(self, spans: List[Dict[str, Any]]) -> (str, float):
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
        txt = line_text.strip()
        if not txt:
            return None

        lower = txt.lower()
        # Skip lines that are obviously metadata or author info
        if any(
            k in lower
            for k in [
                "doi",
                "http",
                "@",
                "received",
                "revised",
                "accepted",
                "published",
                "license",
                "correspondence",
                "copyright",
            ]
        ):
            return None

        # Handle numbered header forms (e.g., "2.1 Methods")
        match = self._header_re.match(txt)
        norm = match.group("h") if match else txt
        norm = self._strip_punct(norm).lower()

        # Direct or substring match to any known header phrase
        for canonical, variants in self.section_aliases.items():
            for variant in variants:
                if norm == variant or norm.startswith(variant + " "):
                    return canonical
                if variant in norm and len(norm) <= 80:
                    return canonical

        # Font-size heuristic (large text likely to be a header)
        if (
            page_median_size
            and line_max_size >= max(page_median_size * 1.25, page_median_size + 2)
            and len(norm) <= 80
        ):
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
        if any(
            k in lower
            for k in [
                "doi",
                "http",
                "license",
                "academic editor",
                "received",
                "revised",
                "accepted",
                "published",
                "correspondence",
                "copyright",
                "basel",
            ]
        ):
            return True
        # Author-like lines (many commas or capitalized short names)
        if text.count(",") >= 2 or len(text.split()) <= 8:
            cap_tokens = sum(
                1 for t in text.split() if re.match(r"^[A-Z][a-zA-Z\-\.]{1,}$", t)
            )
            if cap_tokens >= max(2, len(text.split()) // 3):
                return True
        return False

    # -------------------------------------------------------------------------
    # Metadata extraction
    # -------------------------------------------------------------------------
    def _extract_metadata(self, doc: fitz.Document) -> Dict[str, Any]:
        meta = doc.metadata or {}
        title = meta.get("title") or ""
        author = meta.get("author") or ""
        subject = meta.get("subject") or ""
        keywords = meta.get("keywords") or ""
        page_count = doc.page_count

        if not title:
            try:
                first_page = doc[0]
                candidates = []
                for block in first_page.get_text("dict").get("blocks", []):
                    for line in block.get("lines", []):
                        for span in line.get("spans", []):
                            t = span.get("text", "").strip()
                            s = span.get("size", 0)
                            if len(t) > 8:
                                candidates.append((s, t))
                candidates.sort(key=lambda x: x[0], reverse=True)
                for size, txt in candidates:
                    if txt.count(",") > 2 or "doi" in txt.lower() or "@" in txt:
                        continue
                    title = txt.strip()
                    break
            except Exception:
                pass

        return {
            "title": title or "Unknown",
            "author": author or "Unknown",
            "subject": subject,
            "keywords": keywords,
            "page_count": page_count,
        }

    # -------------------------------------------------------------------------
    # Chunking logic with overlap
    # -------------------------------------------------------------------------
    def _chunk_text(self, text: str) -> List[str]:
        sentences = re.split(r"(?<=[.!?])\s+", text)
        chunks, current = [], ""
        for s in sentences:
            if len(current) + len(s) > self.chunk_size:
                if current:
                    chunks.append(current.strip())
                current = s
            else:
                current = (current + " " + s).strip() if current else s
        if current:
            chunks.append(current.strip())

        if self.overlap > 0 and len(chunks) > 1:
            overlapped = []
            for i, chunk in enumerate(chunks):
                if i == 0:
                    overlapped.append(chunk)
                else:
                    overlap_text = overlapped[-1][-self.overlap :]
                    overlap_text = re.sub(r"^\S*\s", "", overlap_text)
                    overlapped.append((overlap_text + " " + chunk).strip())
            chunks = overlapped
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
