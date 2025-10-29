import fitz  # PyMuPDF
from typing import List, Dict, Any, Tuple
from io import BytesIO
import re
from datetime import datetime

class DocumentProcessor:
    def __init__(self):
        self.chunk_size = 1000
        # Extended section headers with variations
        self.section_headers = {
            "abstract": ["abstract", "summary", "synopsis"],
            "introduction": ["introduction", "background", "overview", "1. introduction", "i. introduction"],
            "methodology": ["methodology", "method", "methods", "materials and methods", "experimental setup", "research methodology"],
            "results": ["results", "findings", "experimental results", "observations"],
            "discussion": ["discussion", "analysis", "evaluation", "interpretation"],
            "conclusion": ["conclusion", "conclusions", "concluding remarks", "future work"],
            "references": ["references", "bibliography", "works cited"]
        }
        # Font characteristics that might indicate a header
        self.header_characteristics = {
            "font_size_threshold": 12,  # Minimum font size for headers
            "is_bold": True,
            "common_header_fonts": ["helvetica-bold", "times-bold", "arial-bold"]
        }

    async def process_pdf(self, file_content: bytes) -> Dict[str, Any]:
        # Create a memory buffer for the PDF content
        pdf_stream = BytesIO(file_content)
        # Open PDF with PyMuPDF
        doc = fitz.open(stream=pdf_stream, filetype="pdf")
        
        # Extract metadata
        metadata = self._extract_metadata(doc)
        
        # Process text by sections
        sections = {}
        current_section = "preamble"
        current_text = []
        
        for page_num, page in enumerate(doc, 1):
            # Get text with more layout information
            blocks = page.get_text("dict")["blocks"]
            for block in blocks:
                if "lines" in block:
                    for line in block["lines"]:
                        for span in line["spans"]:
                            text = span["text"].strip()
                            if not text:
                                continue
                            
                            # Check if this is a section header
                            is_header = self._is_section_header(text.lower())
                            if is_header:
                                current_section = text.lower()
                                sections[current_section] = {
                                    "text": [],
                                    "start_page": page_num
                                }
                            else:
                                if current_section not in sections:
                                    sections[current_section] = {
                                        "text": [],
                                        "start_page": page_num
                                    }
                                sections[current_section]["text"].append(text)
        
        doc.close()
        
        # Process sections into chunks
        processed_sections = {}
        for section, content in sections.items():
            text = " ".join(content["text"])
            chunks = self._chunk_text(text)
            processed_sections[section] = {
                "chunks": chunks,
                "start_page": content["start_page"]
            }
        
        return {
            "metadata": metadata,
            "sections": processed_sections
        }

    def _extract_metadata(self, doc: fitz.Document) -> Dict[str, Any]:
        """Extract metadata from the document"""
        metadata = doc.metadata
        # Try to extract title from first page if not in metadata
        if not metadata.get("title"):
            first_page = doc[0]
            text = first_page.get_text("text")
            # Assume the first line might be the title
            title = text.split("\n")[0].strip()
            metadata["title"] = title
        
        return {
            "title": metadata.get("title", "Unknown"),
            "author": metadata.get("author", "Unknown"),
            "subject": metadata.get("subject", ""),
            "keywords": metadata.get("keywords", ""),
            "page_count": doc.page_count
        }

    def _is_section_header(self, text: str) -> bool:
        """Check if the given text is likely a section header"""
        text = text.lower().strip()
        return any(header in text for header in self.section_headers)

    def _chunk_text(self, text: str) -> List[str]:
        """Split text into chunks with sentence awareness"""
        # First split into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) > self.chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:
                current_chunk = current_chunk + " " + sentence if current_chunk else sentence
        
        if current_chunk:
            chunks.append(current_chunk.strip())
            
        return chunks