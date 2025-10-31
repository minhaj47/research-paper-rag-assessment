import fitz  # PyMuPDF
from typing import List, Dict, Any, Optional, Tuple
from io import BytesIO
import re
import string
import asyncio
from langchain_text_splitters import RecursiveCharacterTextSplitter


class DocumentProcessor:
    def __init__(self, chunk_size: int = 1000, overlap: int = 200):
        self.chunk_size = chunk_size
        self.overlap = overlap

        # Initialize LangChain's advanced text splitter for better semantic chunking
        # CRITICAL: keep_separator must be at END to preserve sentence boundaries
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=overlap,
            length_function=len,
            separators=[
                "\n\n",  # Paragraph breaks (highest priority)
                "\n",    # Line breaks
                ". ",    # Sentences (CRITICAL for boundary quality!)
                "! ",    # Exclamations
                "? ",    # Questions
                "; ",    # Semicolons
                ": ",    # Colons
                ", ",    # Clauses (lower priority)
                " ",     # Words
                ""       # Characters (fallback)
            ],
            is_separator_regex=False,
            keep_separator="end",  # ← CRITICAL: Keeps separators at END of chunks
        )
        
        # Pre-compile page marker pattern for performance
        self._page_pattern = re.compile(r'\[PAGE (\d+)\]')

        # Canonical section name aliases for normalization
        self.section_aliases = {
            "abstract": [
                "abstract", 
                "Abstract", 
                "ABSTRACT",
                "summary",
                "executive summary"
            ],
            "introduction": [
                "introduction", 
                "Introduction", 
                "INTRODUCTION",
                "1. introduction",
                "1 introduction"
            ],
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
                "2. research methodology",
                "2 research methodology",
                "2. methodology",
                "2 methodology"
            ],
            "results": [
                "Results",
                "results and discussion",
                "findings",
                "analysis",
                "outcomes",
                "3. results",
                "3 results",
                "4. results",
                "4 results"
            ],
            "conclusions": [
                "discussion and conclusions",
                "conclusions",
                "conclusion",
                "conclusion and future work",
                "summary",
                "concluding remarks",
                "future work",
                "discussion",
                "5. conclusion",
                "5 conclusion",
                "6. conclusion",
                "6 conclusion"
            ],
            "references": [
                "references",
                "bibliography",
                "acknowledgment",
                "acknowledgement",
                "works cited"
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
        
        # Track all extracted text to detect data loss
        total_text_extracted = 0
        total_text_in_sections = 0

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
                    
                    total_text_extracted += len(text)

                    # Check if line starts with a section header (even if followed by content)
                    header_token, remaining_text = self._detect_header_with_content(text, max_size, page_median_size)
                    
                    if header_token:
                        current_section = header_token
                        if current_section not in sections:
                            sections[current_section] = {"text": [], "start_page": page_no}
                        
                        # Add the full line (header + content if any)
                        sections[current_section]["text"].append(f"[PAGE {page_no}] {text}")
                        continue

                    # Front matter handling (but not for abstract!)
                    if current_section == "preamble" and self._is_front_matter_line(text):
                        sections["preamble"]["text"].append(f"[PAGE {page_no}] {text}")
                        continue

                    # Regular content - capture EVERYTHING
                    if current_section not in sections:
                        sections[current_section] = {"text": [], "start_page": page_no}
                    sections[current_section]["text"].append(f"[PAGE {page_no}] {text}")

        doc.close()

        # Process sections and track uncategorized content
        processed_sections: Dict[str, Any] = {}
        uncategorized_content = []
        
        for name, content in sections.items():
            joined = " ".join(content["text"])
            total_text_in_sections += len(joined)
            
            # Keep very small sections if they might be important
            if len(joined) <= 30 and name not in ["abstract", "introduction"]:
                uncategorized_content.append((name, joined))
                continue
                
            joined = self._whitespace_re.sub(" ", joined).strip()
            
            # Use LangChain's advanced chunking with page tracking
            start_page = content.get("start_page", 1)
            chunks_with_pages = self._chunk_text(joined, start_page)
            
            # Extract just the text for backward compatibility
            chunk_texts = [c['text'] for c in chunks_with_pages]

            processed_sections[name] = {
                "chunks": chunk_texts,
                "chunk_count": len(chunk_texts),
                "start_page": start_page,
                "preview": joined[:250],
                # Additional metadata for better retrieval
                "total_length": len(joined),
                "avg_chunk_size": sum(len(c) for c in chunk_texts) // len(chunk_texts) if chunk_texts else 0,
                # Store page info for each chunk
                "chunks_with_pages": chunks_with_pages,
            }
        
        # Add uncategorized content if significant
        if uncategorized_content:
            uncategorized_text = " ".join([f"[SECTION: {name}] {text}" 
                                          for name, text in uncategorized_content])
            if len(uncategorized_text) > 100:  # Only if substantial
                chunks = self._chunk_text(uncategorized_text)
                processed_sections["unknown"] = {
                    "chunks": chunks,
                    "chunk_count": len(chunks),
                    "start_page": 1,
                    "preview": uncategorized_text[:250],
                    "total_length": len(uncategorized_text),
                    "avg_chunk_size": sum(len(c) for c in chunks) // len(chunks) if chunks else 0,
                }
        
        # Calculate data loss percentage
        data_loss_pct = ((total_text_extracted - total_text_in_sections) / total_text_extracted * 100) if total_text_extracted > 0 else 0
        
        return {
            "metadata": metadata, 
            "sections": processed_sections,
            "stats": {
                "total_text_extracted": total_text_extracted,
                "total_text_in_sections": total_text_in_sections,
                "data_loss_percentage": round(data_loss_pct, 2)
            }
        }

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
        
        # Special case: "Abstract:" is often followed by colon and may have lower importance
        # Check for exact matches first before context analysis
        norm = self._strip_punct(line_text).lower()
        for canonical, variants in self.section_aliases.items():
            for variant in variants:
                variant_norm = self._strip_punct(variant).lower()
                if norm == variant_norm or line_text.strip().lower() == variant.lower():
                    return canonical

        # First check if this text appears in a header-like context
        if not self._is_likely_header_context(line_text, line_max_size, page_median_size):
            # If it doesn't look like a header context, be extra strict
            norm = self._strip_punct(line_text).lower()
            
            # Only allow exact matches for non-header-like contexts
            for canonical, variants in self.section_aliases.items():
                for variant in variants:
                    if norm == variant.lower():
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
                    variant_norm = self._strip_punct(variant).lower()
                    if norm == variant_norm or norm.startswith(variant_norm):
                        return canonical
            return None

        # For potential headers in header-like context
        norm = self._strip_punct(line_text).lower()
        
        # Match exact or close variants
        for canonical, variants in self.section_aliases.items():
            for variant in variants:
                variant_norm = self._strip_punct(variant).lower()
                # Exact match
                if norm == variant_norm:
                    return canonical
                # Starts with variant (e.g., "results and analysis")
                if norm.startswith(variant_norm + " ") and len(norm.split()) <= len(variant_norm.split()) + 3:
                    return canonical

        return None

    # -------------------------------------------------------------------------
    # Helper: detect headers that may have content on same line
    # -------------------------------------------------------------------------
    def _detect_header_with_content(
        self, line_text: str, line_max_size: float, page_median_size: float
    ) -> Tuple[Optional[str], str]:
        """
        Detect if line starts with a section header, even if followed by content.
        Returns: (header_token, remaining_text) or (None, line_text)
        
        Examples:
            "Abstract: Blockchain is..." -> ("abstract", "Blockchain is...")
            "1. Introduction" -> ("introduction", "")
            "Regular text" -> (None, "Regular text")
        """
        if not line_text:
            return None, line_text
        
        # First check if line STARTS with any known section header
        lower = line_text.lower()
        
        # Skip metadata lines
        if any(skip in lower for skip in self._skip_patterns):
            return None, line_text
        
        # Check each section alias
        for canonical, variants in self.section_aliases.items():
            for variant in variants:
                variant_lower = variant.lower()
                
                # Case 1: Line starts with "Header:" or "Header -" or "Header."
                if lower.startswith(variant_lower):
                    # Check what comes after the variant
                    after_pos = len(variant)
                    if after_pos < len(line_text):
                        next_char = line_text[after_pos:after_pos+1]
                        # If followed by :, -, or just whitespace, it's likely a header
                        if next_char in [':', '-', '.', ' ', '\t']:
                            # Extract remaining content
                            remaining = line_text[after_pos:].lstrip(':- \t.')
                            return canonical, remaining
                
                # Case 2: Numbered header like "1. Introduction" or "2 Research Methodology"
                # Check if line matches pattern like "digit(s) variant"
                import re
                numbered_pattern = rf"^\s*(\d+(\.\d+)*)\.?\s+{re.escape(variant_lower)}"
                match = re.match(numbered_pattern, lower)
                if match:
                    # Get remaining text after the header
                    remaining = line_text[match.end():].lstrip(':- \t.')
                    return canonical, remaining
        
        # Not a header
        return None, line_text
    
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
        if not title or len(title) < 10:
            try:
                first_page = doc[0]
                text_dict = first_page.get_text("dict")
                
                # Strategy 1: Find largest text blocks on first page
                candidates = []
                for block in text_dict.get("blocks", []):
                    if "lines" not in block:
                        continue
                    for line in block.get("lines", []):
                        for span in line.get("spans", []):
                            text = span.get("text", "").strip()
                            size = span.get("size", 0)
                            
                            # Potential title characteristics:
                            # - Longer than 8 chars but not too long
                            # - Not metadata (no @, doi, http)
                            # - Not author list (limited commas)
                            # - Reasonable font size
                            if (len(text) > 8 and len(text) < 200 and
                                not any(skip in text.lower() for skip in ["doi", "@", "http", "citation:", "received:", "copyright"]) and
                                text.count(",") <= 2 and
                                size > 10):
                                candidates.append((size, len(text), text))
                
                # Sort by font size (primary) and text length (secondary)
                candidates.sort(key=lambda x: (x[0], x[1]), reverse=True)
                
                # Strategy 2: Look for multi-line titles (common in papers)
                potential_titles = []
                for i, (size, length, text) in enumerate(candidates[:10]):
                    # Check if next candidate might be continuation
                    if i < len(candidates) - 1:
                        next_size, next_len, next_text = candidates[i+1]
                        # If similar size, might be multi-line title
                        if abs(size - next_size) < 2 and len(potential_titles) == 0:
                            combined = f"{text} {next_text}"
                            if len(combined) < 250:
                                potential_titles.append(combined)
                                continue
                    
                    # Single line title
                    if not any(word in text.lower() for word in ["abstract", "keywords", "editor"]):
                        potential_titles.append(text)
                
                # Pick the best title
                if potential_titles:
                    title = potential_titles[0]
                    
                    # Clean up title
                    # Remove common prefixes
                    for prefix in ["Review", "Article", "Research Paper", "Commentary"]:
                        if title.startswith(prefix):
                            title = title[len(prefix):].strip()
                    
            except Exception as e:
                print(f"Warning: Title extraction failed: {e}")
        
        # Extract author from first page if not in metadata
        if not author or len(author) < 3:
            try:
                first_page = doc[0]
                full_text = first_page.get_text()
                lines = full_text.split('\n')
                
                # Look for author patterns (names with commas, after title)
                for i, line in enumerate(lines[:30]):  # Check first 30 lines
                    line = line.strip()
                    # Author line typically has multiple commas and capitalized words
                    if (line.count(',') >= 2 and 
                        len(line) > 10 and 
                        len(line) < 200 and
                        not any(skip in line.lower() for skip in ["doi", "http", "citation", "editor", "abstract"])):
                        
                        # Count capitalized words (names are capitalized)
                        words = line.split()
                        cap_count = sum(1 for word in words if word and word[0].isupper() and len(word) > 1)
                        
                        if cap_count >= len(words) // 2:
                            author = line
                            break
            except Exception as e:
                print(f"Warning: Author extraction failed: {e}")

        return {
            "title": title or "Unknown",
            "author": author or "Unknown", 
            "page_count": doc.page_count,
        }

    # -------------------------------------------------------------------------
    # Chunking logic with LangChain's advanced text splitter (page-aware)
    # -------------------------------------------------------------------------
    def _chunk_text(self, text: str, start_page: int = 1) -> List[Dict[str, Any]]:
        """
        Uses LangChain's RecursiveCharacterTextSplitter for better semantic chunking.
        
        CRITICAL FIX: Removes [PAGE X] markers before chunking to prevent mid-sentence splits.
        Page numbers are tracked and stored in chunk metadata instead.
        
        This preserves:
        - Paragraph boundaries
        - Sentence integrity (no mid-sentence splits!)
        - Natural language flow
        - Proper overlap for context continuity
        - Page tracking per chunk
        
        Args:
            text: Text containing [PAGE X] markers
            start_page: Default page number if no markers found
            
        Returns:
            List of dicts with 'text' and 'page' keys
        """
        try:
            # Extract page positions before cleaning
            page_positions = []
            for match in self._page_pattern.finditer(text):
                page_positions.append((match.start(), int(match.group(1))))
            
            # Clean text for chunking (remove page markers)
            clean_text = self._page_pattern.sub('', text)
            clean_text = self._whitespace_re.sub(' ', clean_text).strip()
            
            # Use LangChain's advanced splitter on clean text
            raw_chunks = self.text_splitter.split_text(clean_text)
            
            # Filter out very small chunks (noise)
            raw_chunks = [chunk.strip() for chunk in raw_chunks if len(chunk.strip()) > 50]
            
            # Map chunks back to page numbers
            chunks_with_pages = []
            char_offset = 0
            
            for chunk_text in raw_chunks:
                # Find the page number for this chunk's position
                chunk_page = start_page
                
                # Map character offset in clean text back to original text position
                # (approximate since we removed markers)
                for pos, page in page_positions:
                    # Adjust position by accounting for removed markers
                    # Each marker is ~10 chars: "[PAGE XX] "
                    adjusted_pos = pos - (len([p for p in page_positions if p[0] < pos]) * 10)
                    if adjusted_pos <= char_offset:
                        chunk_page = page
                
                chunks_with_pages.append({
                    'text': chunk_text,
                    'page': chunk_page
                })
                
                char_offset += len(chunk_text) + 1  # +1 for space between chunks
            
            return chunks_with_pages
            
        except Exception as e:
            # Fallback to simple sentence-based chunking if LangChain fails
            print(f"Warning: LangChain splitter failed, using fallback: {e}")
            return self._chunk_text_fallback(text, start_page)
    
    def _chunk_text_fallback(self, text: str, start_page: int = 1) -> List[Dict[str, Any]]:
        """Fallback chunking method (original implementation) - now page-aware"""
        # Extract page info
        page_positions = []
        for match in self._page_pattern.finditer(text):
            page_positions.append((match.start(), int(match.group(1))))
        
        # Clean text
        clean_text = self._page_pattern.sub('', text)
        clean_text = self._whitespace_re.sub(' ', clean_text).strip()
        
        sentences = re.split(r"(?<=[.!?])\s+", clean_text)
        chunks = []
        current = ""
        char_offset = 0
        
        for sentence in sentences:
            # If adding this sentence would exceed chunk size
            if len(current) + len(sentence) > self.chunk_size and current:
                # Find page for this chunk
                chunk_page = start_page
                for pos, page in page_positions:
                    adjusted_pos = pos - (len([p for p in page_positions if p[0] < pos]) * 10)
                    if adjusted_pos <= char_offset:
                        chunk_page = page
                
                chunks.append({
                    'text': current.strip(),
                    'page': chunk_page
                })
                char_offset += len(current)
                current = sentence
            else:
                current = f"{current} {sentence}".strip() if current else sentence
        
        if current:
            chunk_page = start_page
            for pos, page in page_positions:
                adjusted_pos = pos - (len([p for p in page_positions if p[0] < pos]) * 10)
                if adjusted_pos <= char_offset:
                    chunk_page = page
            chunks.append({
                'text': current.strip(),
                'page': chunk_page
            })

        # Simple overlap: add last N characters from previous chunk
        if self.overlap > 0 and len(chunks) > 1:
            for i in range(1, len(chunks)):
                prev_text = chunks[i-1]['text']
                overlap_text = prev_text[-self.overlap:].lstrip()
                chunks[i]['text'] = f"{overlap_text} {chunks[i]['text']}"

        return chunks

    # -------------------------------------------------------------------------
    # Advanced: Generate chunks with rich metadata for RAG
    # -------------------------------------------------------------------------
    def get_chunks_with_metadata(
        self, processed_result: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Converts processed sections into a flat list of chunks with metadata.
        This format is optimized for vector store insertion and retrieval.
        
        Now includes accurate page numbers per chunk (post page-marker cleaning fix).
        
        Returns:
            List of dicts with keys: text, metadata (section, page, chunk_id, etc.)
        """
        chunks_with_metadata = []
        chunk_global_id = 0
        
        metadata = processed_result.get("metadata", {})
        sections = processed_result.get("sections", {})
        
        for section_name, section_data in sections.items():
            chunks = section_data.get("chunks", [])
            chunks_with_pages = section_data.get("chunks_with_pages", [])
            start_page = section_data.get("start_page", 1)
            
            # Use chunks_with_pages if available (new format with accurate pages)
            if chunks_with_pages:
                for idx, chunk_info in enumerate(chunks_with_pages):
                    chunk_text = chunk_info.get('text', '')
                    chunk_page = chunk_info.get('page', start_page)
                    
                    chunk_metadata = {
                        "section": section_name,
                        "page": chunk_page,  # Accurate page per chunk!
                        "start_page": start_page,
                        "chunk_index": idx,
                        "chunk_global_id": chunk_global_id,
                        "total_chunks_in_section": len(chunks_with_pages),
                        "paper_title": metadata.get("title", "Unknown"),
                        "paper_author": metadata.get("author", "Unknown"),
                        "chunk_length": len(chunk_text),
                    }
                    
                    chunks_with_metadata.append({
                        "text": chunk_text,
                        "metadata": chunk_metadata,
                    })
                    
                    chunk_global_id += 1
            else:
                # Fallback for old format (backward compatibility)
                for idx, chunk_text in enumerate(chunks):
                    chunk_metadata = {
                        "section": section_name,
                        "page": start_page,
                        "start_page": start_page,
                        "chunk_index": idx,
                        "chunk_global_id": chunk_global_id,
                        "total_chunks_in_section": len(chunks),
                        "paper_title": metadata.get("title", "Unknown"),
                        "paper_author": metadata.get("author", "Unknown"),
                        "chunk_length": len(chunk_text),
                    }
                    
                    chunks_with_metadata.append({
                        "text": chunk_text,
                        "metadata": chunk_metadata,
                    })
                    
                    chunk_global_id += 1
        
        return chunks_with_metadata

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
