"""
More detailed diagnostic to trace header detection
"""
import fitz

doc = fitz.open("sample_papers/paper_1.pdf")
first_page = doc[0]
blocks = first_page.get_text("dict").get("blocks", [])

print("="*80)
print("🔍 Tracing Header Detection for 'Abstract'")
print("="*80)

# Calculate median font size
sizes = [
    span.get("size", 0)
    for block in blocks
    for line in block.get("lines", [])
    for span in line.get("spans", [])
]
page_median_size = sorted(sizes)[len(sizes)//2] if sizes else 0
print(f"\n📏 Page median font size: {page_median_size}")

# Find the Abstract line
for block in blocks:
    if "lines" not in block:
        continue
    for line in block["lines"]:
        spans = line.get("spans", [])
        if not spans:
            continue
        
        # Merge spans
        text = ""
        max_size = 0.0
        for span in spans:
            s_text = span.get("text", "").strip()
            size = span.get("size", 0)
            max_size = max(max_size, size)
            if s_text:
                text += (" " if text else "") + s_text
        
        text = text.strip()
        
        if "abstract" in text.lower():
            print(f"\n📋 Found line with 'abstract':")
            print(f"   Text: '{text}'")
            print(f"   Length: {len(text)} chars, {len(text.split())} words")
            print(f"   Font Size: {max_size}")
            print(f"   Median Size: {page_median_size}")
            print(f"   Size Ratio: {max_size / page_median_size if page_median_size > 0 else 0:.2f}")
            
            # Test if it would be detected
            print(f"\n🧪 Detection Tests:")
            print(f"   - Length check (< 150): {len(text) < 150}")
            print(f"   - Word count (< 20): {len(text.split()) < 20}")
            print(f"   - Has 'abstract': {'abstract' in text.lower()}")
            print(f"   - Starts with 'Abstract': {text.lower().startswith('abstract')}")
            print(f"   - Ends with colon: {text.strip().endswith(':')}")
            
            # Check context
            print(f"\n🔍 Context Analysis:")
            words = text.split()
            print(f"   - Short text (<=3 words): {len(words) <= 3}")
            print(f"   - Font larger (>= 1.3x median): {max_size >= page_median_size * 1.3}")
            
doc.close()
