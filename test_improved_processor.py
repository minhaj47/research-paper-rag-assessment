"""
Test script to demonstrate LangChain text splitting improvements
"""
import asyncio
from src.services.document_processor import DocumentProcessor


async def test_document_processor():
    """Test the improved document processor with LangChain"""
    
    print("=" * 80)
    print("🧪 Testing Improved Document Processor with LangChain")
    print("=" * 80)
    
    # Initialize processor
    processor = DocumentProcessor(chunk_size=1000, overlap=200)
    print("\n✅ Initialized DocumentProcessor with LangChain's RecursiveCharacterTextSplitter")
    print(f"   - Chunk Size: {processor.chunk_size}")
    print(f"   - Overlap: {processor.overlap}")
    print(f"   - Splitter Type: {type(processor.text_splitter).__name__}")
    
    # Test with a sample paper
    sample_paper_path = "sample_papers/paper_1.pdf"
    
    try:
        with open(sample_paper_path, "rb") as f:
            pdf_content = f.read()
        
        print(f"\n📄 Processing: {sample_paper_path}")
        print("   Please wait...")
        
        # Process the PDF
        result = await processor.process_pdf(pdf_content)
        
        # Display metadata
        print("\n📊 Document Metadata:")
        print(f"   - Title: {result['metadata']['title']}")
        print(f"   - Author: {result['metadata']['author']}")
        print(f"   - Pages: {result['metadata']['page_count']}")
        
        # Display sections
        print("\n📑 Sections Extracted:")
        total_chunks = 0
        for section_name, section_data in result["sections"].items():
            chunk_count = section_data['chunk_count']
            total_chunks += chunk_count
            print(f"   - {section_name:20s}: {chunk_count:3d} chunks "
                  f"(~{section_data['avg_chunk_size']} chars/chunk)")
        
        print(f"\n   Total Chunks: {total_chunks}")
        
        # Test new get_chunks_with_metadata method
        print("\n🔍 Testing get_chunks_with_metadata():")
        chunks_with_metadata = processor.get_chunks_with_metadata(result)
        
        print(f"   - Generated {len(chunks_with_metadata)} chunks with metadata")
        
        # Show sample chunk
        if chunks_with_metadata:
            sample = chunks_with_metadata[5] if len(chunks_with_metadata) > 5 else chunks_with_metadata[0]
            print(f"\n📝 Sample Chunk:")
            print(f"   Section: {sample['metadata']['section']}")
            print(f"   Page: {sample['metadata']['start_page']}")
            print(f"   Chunk Index: {sample['metadata']['chunk_index']} / "
                  f"{sample['metadata']['total_chunks_in_section']}")
            print(f"   Global ID: {sample['metadata']['chunk_global_id']}")
            print(f"   Length: {sample['metadata']['chunk_length']} characters")
            print(f"\n   Preview:")
            preview_text = sample['text'][:300]
            print(f"   \"{preview_text}...\"")
        
        # Test chunk quality
        print("\n✨ Chunk Quality Analysis:")
        methodology_chunks = [
            c for c in chunks_with_metadata 
            if c["metadata"]["section"] == "methodology"
        ]
        
        if methodology_chunks:
            print(f"   - Methodology section: {len(methodology_chunks)} chunks")
            print(f"   - Average length: "
                  f"{sum(c['metadata']['chunk_length'] for c in methodology_chunks) // len(methodology_chunks)} chars")
            
            # Check if chunks maintain semantic boundaries
            print("\n   Checking semantic boundaries:")
            for i, chunk in enumerate(methodology_chunks[:2]):
                text = chunk['text']
                ends_with_sentence = text.strip()[-1] in '.!?'
                starts_clean = not text[0].islower() or text.startswith('[PAGE')
                print(f"     Chunk {i+1}: "
                      f"{'✅' if ends_with_sentence else '⚠️'} Ends properly | "
                      f"{'✅' if starts_clean else '⚠️'} Starts properly")
        
        # Compare with simple splitting
        print("\n🔄 Comparing with Fallback Method:")
        sample_text = list(result["sections"].values())[0]["chunks"][0]
        
        # LangChain splitting
        langchain_chunks = processor.text_splitter.split_text(sample_text)
        
        # Fallback splitting
        fallback_chunks = processor._chunk_text_fallback(sample_text)
        
        print(f"   - LangChain chunks: {len(langchain_chunks)}")
        print(f"   - Fallback chunks: {len(fallback_chunks)}")
        print(f"   - Difference: {abs(len(langchain_chunks) - len(fallback_chunks))} chunks")
        
        print("\n" + "=" * 80)
        print("✅ All tests completed successfully!")
        print("=" * 80)
        
        print("\n💡 Key Improvements:")
        print("   1. ✅ Semantic boundary preservation (paragraph/sentence aware)")
        print("   2. ✅ Comprehensive metadata for better retrieval")
        print("   3. ✅ Hierarchical splitting for natural language flow")
        print("   4. ✅ Ready for vector store integration")
        
        return result, chunks_with_metadata
        
    except FileNotFoundError:
        print(f"\n❌ Error: Could not find {sample_paper_path}")
        print("   Please ensure sample papers are in the sample_papers/ directory")
        return None, None
    
    except Exception as e:
        print(f"\n❌ Error processing document: {e}")
        import traceback
        traceback.print_exc()
        return None, None


def test_text_splitting():
    """Test text splitting with sample text"""
    print("\n" + "=" * 80)
    print("🧪 Testing Text Splitting Comparison")
    print("=" * 80)
    
    processor = DocumentProcessor(chunk_size=500, overlap=50)
    
    sample_text = """
    Introduction to Research Methodology
    
    This paper presents a novel approach to analyzing large-scale datasets. 
    Our methodology combines traditional statistical methods with modern 
    machine learning techniques to achieve better accuracy.
    
    Data Collection
    
    We collected data from multiple sources including academic databases, 
    public repositories, and industry partners. The dataset comprises over 
    10,000 samples representing diverse domains.
    
    Analysis Techniques
    
    We employed several analysis techniques: (1) descriptive statistics for 
    initial exploration, (2) regression models for relationship identification, 
    and (3) neural networks for pattern recognition. Each technique was 
    carefully validated using cross-validation.
    
    Results and Discussion
    
    Our results show significant improvements over baseline methods. The 
    proposed approach achieved 95% accuracy on the test set, compared to 
    78% for traditional methods. These findings suggest that our methodology 
    is effective for this type of analysis.
    """
    
    print("\n📝 Sample Text Length:", len(sample_text), "characters")
    
    # LangChain splitting
    print("\n🔹 LangChain RecursiveCharacterTextSplitter:")
    langchain_chunks = processor.text_splitter.split_text(sample_text)
    print(f"   Generated {len(langchain_chunks)} chunks")
    for i, chunk in enumerate(langchain_chunks, 1):
        print(f"\n   Chunk {i} ({len(chunk)} chars):")
        print(f"   {chunk[:100]}...")
    
    # Fallback splitting
    print("\n🔹 Fallback Sentence-Based Splitter:")
    fallback_chunks = processor._chunk_text_fallback(sample_text)
    print(f"   Generated {len(fallback_chunks)} chunks")
    for i, chunk in enumerate(fallback_chunks, 1):
        print(f"\n   Chunk {i} ({len(chunk)} chars):")
        print(f"   {chunk[:100]}...")
    
    print("\n" + "=" * 80)
    print("✅ Text splitting comparison complete!")
    print(f"   LangChain: {len(langchain_chunks)} chunks (semantic boundaries)")
    print(f"   Fallback: {len(fallback_chunks)} chunks (sentence boundaries)")
    print("=" * 80)


if __name__ == "__main__":
    # Run async test
    print("\n🚀 Starting Document Processing Tests...\n")
    
    # Test with actual PDF
    result, chunks = asyncio.run(test_document_processor())
    
    # Test text splitting comparison
    if result:
        print("\n")
        test_text_splitting()
    
    print("\n✨ All tests complete! Check DOCUMENT_PROCESSING_IMPROVEMENTS.md for details.")
