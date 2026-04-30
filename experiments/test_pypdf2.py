"""
PyPDF2 - Basic text extraction approach
Pros: Simple, lightweight
Cons: No layout preservation, loses positioning
"""

from PyPDF2 import PdfReader
import json

def extract_with_pypdf2(pdf_path):
    reader = PdfReader(pdf_path)

    all_text = []
    for page_num, page in enumerate(reader.pages, 1):
        text = page.extract_text()
        all_text.append({
            "page": page_num,
            "text": text
        })

    return all_text

if __name__ == "__main__":
    pdf_path = "../data/espn_bet.pdf"

    print("=" * 60)
    print("PyPDF2 Extraction")
    print("=" * 60)

    result = extract_with_pypdf2(pdf_path)

    # Show first page sample
    print(f"\nTotal pages: {len(result)}")
    print(f"\nFirst page preview (first 500 chars):")
    print("-" * 60)
    print(result[0]["text"][:500])
    print("-" * 60)

    # Save full output
    with open("pypdf2_output.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print("\nFull output saved to: experiments/pypdf2_output.json")
