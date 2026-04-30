"""
PyMuPDF (fitz) - Fast extraction with positioning
Pros: Very fast, excellent positioning data, good for structured layouts
Cons: More complex coordinate system
"""

import fitz  # PyMuPDF
import json

def extract_with_pymupdf(pdf_path):
    doc = fitz.open(pdf_path)
    results = []

    for page_num in range(len(doc)):
        page = doc[page_num]

        # Extract text
        text = page.get_text()

        # Extract text with positioning (blocks)
        blocks = page.get_text("blocks")

        # Extract text with detailed positioning (dict format)
        text_dict = page.get_text("dict")

        results.append({
            "page": page_num + 1,
            "text": text,
            "blocks_count": len(blocks),
            "sample_blocks": [
                {
                    "bbox": block[:4],
                    "text": block[4][:100]  # First 100 chars
                }
                for block in blocks[:5]  # First 5 blocks
            ]
        })

    doc.close()
    return results

if __name__ == "__main__":
    pdf_path = "../data/espn_bet.pdf"

    print("=" * 60)
    print("PyMuPDF (fitz) Extraction")
    print("=" * 60)

    result = extract_with_pymupdf(pdf_path)

    # Show first page sample
    print(f"\nTotal pages: {len(result)}")
    print(f"\nFirst page info:")
    print(f"  Text blocks found: {result[0]['blocks_count']}")
    print(f"\nFirst page preview (first 500 chars):")
    print("-" * 60)
    print(result[0]["text"][:500])
    print("-" * 60)

    # Save full output
    with open("pymupdf_output.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print("\nFull output saved to: experiments/pymupdf_output.json")
