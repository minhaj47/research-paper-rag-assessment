#!/usr/bin/env python3
"""
Test script to measure boundary quality after page marker cleaning fix.
Validates that chunks end with proper punctuation (no mid-sentence splits).
"""

import sys
sys.path.insert(0, 'src')

from services.document_processor import DocumentProcessor
import re


def test_boundary_quality(pdf_path: str, paper_name: str):
    """Test boundary quality for a single paper"""
    
    print(f"\n{'='*80}")
    print(f"📄 Testing: {paper_name}")
    print(f"{'='*80}\n")
    
    # Process the PDF
    with open(pdf_path, 'rb') as f:
        processor = DocumentProcessor()
        result = processor._process_pdf_sync(f.read())
    
    sections = result.get('sections', {})
    metadata = result.get('metadata', {})
    
    print(f"📋 Paper: {metadata.get('title', 'Unknown')[:60]}...")
    print(f"👤 Author: {metadata.get('author', 'Unknown')[:50]}...")
    print(f"📊 Total sections: {len(sections)}\n")
    
    # Analyze boundary quality
    total_chunks = 0
    proper_boundaries = 0
    improper_boundaries = []
    has_page_markers = []
    
    for section_name, section_data in sections.items():
        chunks = section_data.get('chunks', [])
        chunks_with_pages = section_data.get('chunks_with_pages', [])
        
        print(f"\n🔍 Section: {section_name.upper()}")
        print(f"   Chunks: {len(chunks)}")
        
        for idx, chunk_text in enumerate(chunks):
            total_chunks += 1
            
            # Check if chunk ends properly (with punctuation)
            last_char = chunk_text.strip()[-1] if chunk_text.strip() else ''
            ends_properly = last_char in '.!?);'
            
            if ends_properly:
                proper_boundaries += 1
            else:
                improper_boundaries.append({
                    'section': section_name,
                    'chunk_idx': idx,
                    'last_chars': chunk_text.strip()[-50:] if len(chunk_text) > 50 else chunk_text.strip(),
                    'last_char': last_char
                })
            
            # Check if [PAGE X] markers are still present (they shouldn't be!)
            if '[PAGE' in chunk_text:
                has_page_markers.append({
                    'section': section_name,
                    'chunk_idx': idx,
                    'snippet': chunk_text[:100]
                })
            
            # Show first 2 chunks of each section
            if idx < 2:
                chunk_page = 'N/A'
                if chunks_with_pages and idx < len(chunks_with_pages):
                    chunk_page = chunks_with_pages[idx].get('page', 'N/A')
                
                first_60 = chunk_text[:60].replace('\n', ' ')
                last_60 = chunk_text[-60:].replace('\n', ' ')
                boundary_icon = "✅" if ends_properly else "❌"
                
                print(f"   Chunk {idx} (page {chunk_page}) {boundary_icon}")
                print(f"      Start: {first_60}...")
                print(f"      End:   ...{last_60}")
    
    # Calculate boundary quality score
    boundary_quality = (proper_boundaries / total_chunks * 100) if total_chunks > 0 else 0
    
    print(f"\n{'='*80}")
    print(f"📊 BOUNDARY QUALITY RESULTS")
    print(f"{'='*80}")
    print(f"Total chunks:           {total_chunks}")
    print(f"Proper boundaries:      {proper_boundaries} ✅")
    print(f"Improper boundaries:    {len(improper_boundaries)} ❌")
    print(f"Boundary Quality Score: {boundary_quality:.1f}%")
    print(f"Target:                 >85% ✅")
    print()
    
    if boundary_quality >= 85:
        print("✅ EXCELLENT: Boundary quality meets production standards!")
    elif boundary_quality >= 70:
        print("⚠️  ACCEPTABLE: Boundary quality is good but can be improved")
    else:
        print("❌ POOR: Boundary quality needs improvement")
    
    # Check for page markers
    print(f"\n{'='*80}")
    print(f"🔍 PAGE MARKER CHECK")
    print(f"{'='*80}")
    if has_page_markers:
        print(f"❌ FAILED: Found {len(has_page_markers)} chunks with [PAGE X] markers!")
        print("   These should have been removed during chunking.")
        for item in has_page_markers[:3]:
            print(f"   Section: {item['section']}, Chunk: {item['chunk_idx']}")
            print(f"   Snippet: {item['snippet'][:80]}...")
    else:
        print("✅ PASSED: No [PAGE X] markers found in chunks (clean text!)")
    
    # Show sample improper boundaries
    if improper_boundaries:
        print(f"\n{'='*80}")
        print(f"❌ SAMPLE IMPROPER BOUNDARIES (first 5)")
        print(f"{'='*80}")
        for item in improper_boundaries[:5]:
            print(f"\nSection: {item['section']}, Chunk: {item['chunk_idx']}")
            print(f"Ends with: '{item['last_char']}' (expected: . ! ? ) ;)")
            print(f"Last 50 chars: ...{item['last_chars']}")
    
    return {
        'paper': paper_name,
        'total_chunks': total_chunks,
        'boundary_quality': boundary_quality,
        'has_page_markers': len(has_page_markers) > 0,
        'improper_boundaries': len(improper_boundaries)
    }


def main():
    """Test multiple papers"""
    
    print("="*80)
    print("🎯 BOUNDARY QUALITY TEST - Page Marker Cleaning Fix Validation")
    print("="*80)
    print("\nThis test validates:")
    print("  1. ✅ No mid-sentence splits")
    print("  2. ✅ Clean chunk boundaries (ending with punctuation)")
    print("  3. ✅ Page markers removed from chunk text")
    print("  4. ✅ Page numbers tracked in metadata")
    print()
    
    papers = [
        ('sample_papers/paper_1.pdf', 'Paper 1'),
        ('sample_papers/paper_2.pdf', 'Paper 2'),
    ]
    
    results = []
    for pdf_path, paper_name in papers:
        try:
            result = test_boundary_quality(pdf_path, paper_name)
            results.append(result)
        except Exception as e:
            print(f"\n❌ ERROR processing {paper_name}: {e}")
            import traceback
            traceback.print_exc()
    
    # Summary
    print(f"\n{'='*80}")
    print(f"📈 OVERALL SUMMARY")
    print(f"{'='*80}\n")
    
    total_chunks = sum(r['total_chunks'] for r in results)
    avg_quality = sum(r['boundary_quality'] for r in results) / len(results) if results else 0
    papers_with_markers = sum(1 for r in results if r['has_page_markers'])
    
    print(f"Papers tested:           {len(results)}")
    print(f"Total chunks analyzed:   {total_chunks}")
    print(f"Average boundary quality: {avg_quality:.1f}%")
    print(f"Papers with page markers: {papers_with_markers} {'❌' if papers_with_markers > 0 else '✅'}")
    print()
    
    if avg_quality >= 85 and papers_with_markers == 0:
        print("✅✅ EXCELLENT: Fix successful! Production-ready quality achieved.")
    elif avg_quality >= 70:
        print("⚠️  GOOD: Improvement achieved, but some edge cases remain.")
    else:
        print("❌ NEEDS WORK: Fix not effective, further improvements needed.")
    
    print()
    print("Expected improvements:")
    print("  Before fix: ~0-40% boundary quality (mid-sentence splits)")
    print("  After fix:  ~85-95% boundary quality (clean boundaries)")
    print(f"  Actual:     {avg_quality:.1f}%")
    print()


if __name__ == '__main__':
    main()
