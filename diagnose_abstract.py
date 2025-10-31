"""
Diagnostic script to find why Abstract section is missing
"""
import asyncio
from src.services.document_processor import DocumentProcessor
import fitz


async def diagnose_abstract_detection():
    print("="*80)
    print("🔍 DIAGNOSTIC: Abstract Detection")
    print("="*80)
    
    # Open PDF and check first page
    doc = fitz.open("sample_papers/paper_1.pdf")
    first_page = doc[0]
    
    print("\n📄 First Page Text (checking for 'Abstract'):") 
    full_text = first_page.get_text()
    
    # Find abstract
    abstract_pos = full_text.lower().find("abstract")
    if abstract_pos >= 0:
        print(f"\n✅ Found 'Abstract' at position {abstract_pos}")
        print(f"Context:\n{full_text[max(0, abstract_pos-50):abstract_pos+500]}")
    else:
        print("\n❌ 'Abstract' not found in first page text!")
    
    # Check structured text
    print("\n\n📋 Checking Block Structure:")
    blocks = first_page.get_text("dict").get("blocks", [])
    
    found_abstract = False
    for block_idx, block in enumerate(blocks):
        if "lines" not in block:
            continue
        for line_idx, line in enumerate(block["lines"]):
            for span_idx, span in enumerate(line.get("spans", [])):
                text = span.get("text", "").strip()
                if "abstract" in text.lower():
                    size = span.get("size", 0)
                    print(f"\n✅ Found in Block {block_idx}, Line {line_idx}, Span {span_idx}")
                    print(f"   Text: '{text}'")
                    print(f"   Font Size: {size}")
                    print(f"   Full Line:")
                    full_line = " ".join([s.get("text", "") for s in line.get("spans", [])])
                    print(f"   '{full_line.strip()}'")
                    found_abstract = True
    
    if not found_abstract:
        print("\n❌ 'Abstract' not found in structured blocks!")
    
    doc.close()
    
    # Now test with processor
    print("\n\n🔧 Testing Document Processor:")
    processor = DocumentProcessor()
    
    with open("sample_papers/paper_1.pdf", "rb") as f:
        result = await processor.process_pdf(f.read())
    
    print(f"\n📊 Sections Detected:")
    for section_name in result["sections"].keys():
        chunk_count = result["sections"][section_name]["chunk_count"]
        preview = result["sections"][section_name]["preview"][:100]
        print(f"   - {section_name}: {chunk_count} chunks")
        print(f"     Preview: {preview}...")
    
    if "abstract" in result["sections"]:
        print("\n✅ SUCCESS: Abstract section found!")
        abstract_data = result["sections"]["abstract"]
        print(f"   Chunks: {abstract_data['chunk_count']}")
        print(f"   Preview: {abstract_data['preview'][:200]}...")
    else:
        print("\n❌ PROBLEM: Abstract section NOT found in processed results!")
        print("\n🔍 Checking if abstract content is in other sections...")
        
        for section_name, section_data in result["sections"].items():
            preview = section_data["preview"].lower()
            if "blockchain is a peer-to-peer" in preview:
                print(f"\n⚠️  Abstract content found in '{section_name}' section!")
                print(f"   Preview: {section_data['preview'][:300]}...")
    
    # Check data loss
    if "stats" in result:
        stats = result["stats"]
        print(f"\n📈 Data Loss Statistics:")
        print(f"   Total extracted: {stats['total_text_extracted']} chars")
        print(f"   In sections: {stats['total_text_in_sections']} chars")
        print(f"   Data loss: {stats['data_loss_percentage']}%")


if __name__ == "__main__":
    asyncio.run(diagnose_abstract_detection())
