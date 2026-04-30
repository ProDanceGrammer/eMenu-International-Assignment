"""
pdfminer.six - Detailed text positioning for complex layouts
Pros: Very detailed positioning, handles complex layouts well
Cons: Slower, more complex API, steeper learning curve
"""

from pdfminer.high_level import extract_text, extract_pages
from pdfminer.layout import LAParams, LTTextContainer, LTChar
import json

def extract_with_pdfminer(pdf_path):
    results = []

    # Basic text extraction
    full_text = extract_text(pdf_path)

    # Detailed extraction with layout analysis
    laparams = LAParams()

    for page_num, page_layout in enumerate(extract_pages(pdf_path, laparams=laparams), 1):
        page_text = []
        elements = []

        for element in page_layout:
            if isinstance(element, LTTextContainer):
                text = element.get_text()
                bbox = element.bbox

                elements.append({
                    "bbox": bbox,
                    "text": text[:100]  # First 100 chars
                })
                page_text.append(text)

        results.append({
            "page": page_num,
            "text": "".join(page_text),
            "elements_count": len(elements),
            "sample_elements": elements[:5]  # First 5 elements
        })

    return results

if __name__ == "__main__":
    pdf_path = "../data/espn_bet.pdf"

    print("=" * 60)
    print("pdfminer.six Extraction")
    print("=" * 60)

    result = extract_with_pdfminer(pdf_path)

    # Show first page sample
    print(f"\nTotal pages: {len(result)}")
    print(f"\nFirst page info:")
    print(f"  Text elements found: {result[0]['elements_count']}")
    print(f"\nFirst page preview (first 500 chars):")
    print("-" * 60)
    print(result[0]["text"][:500])
    print("-" * 60)

    # Save full output
    with open("pdfminer_output.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print("\nFull output saved to: experiments/pdfminer_output.json")
