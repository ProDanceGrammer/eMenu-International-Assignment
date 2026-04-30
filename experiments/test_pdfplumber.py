"""
pdfplumber - Layout-aware extraction with column detection
Pros: Preserves layout, can detect tables and columns
Cons: Slower than PyMuPDF, more complex API
"""

import pdfplumber
import json

def extract_with_pdfplumber(pdf_path):
    results = []

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, 1):
            # Extract text with layout
            text = page.extract_text()

            # Extract text with positioning
            words = page.extract_words()

            # Try to detect tables
            tables = page.extract_tables()

            results.append({
                "page": page_num,
                "text": text,
                "word_count": len(words),
                "tables_found": len(tables),
                "sample_words": words[:10] if words else []  # First 10 words with positions
            })

    return results

if __name__ == "__main__":
    pdf_path = "../data/espn_bet.pdf"

    print("=" * 60)
    print("pdfplumber Extraction")
    print("=" * 60)

    result = extract_with_pdfplumber(pdf_path)

    # Show first page sample
    print(f"\nTotal pages: {len(result)}")
    print(f"\nFirst page info:")
    print(f"  Words extracted: {result[0]['word_count']}")
    print(f"  Tables found: {result[0]['tables_found']}")
    print(f"\nFirst page preview (first 500 chars):")
    print("-" * 60)
    print(result[0]["text"][:500])
    print("-" * 60)

    # Save full output
    with open("pdfplumber_output.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print("\nFull output saved to: experiments/pdfplumber_output.json")
