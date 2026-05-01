"""
Menu Extractor Module

Main orchestration module that coordinates PDF parsing, data normalization,
and JSON output generation.
"""

import json
from pathlib import Path
from typing import List, Dict, Any

from .parser import PDFParser
from .normalizer import DataNormalizer


class MenuExtractor:
    """Main extractor class for processing menu PDFs."""

    def __init__(self, pdf_path: str, output_path: str = "output/menu_data.json"):
        """
        Initialize menu extractor.

        Args:
            pdf_path: Path to input PDF file
            output_path: Path for output JSON file
        """
        self.pdf_path = pdf_path
        self.output_path = output_path
        self.parser = PDFParser(pdf_path)
        self.normalizer = DataNormalizer()

    def extract(self) -> List[Dict[str, Any]]:
        """
        Extract menu data from PDF.

        Returns:
            List of dish dictionaries

        Raises:
            FileNotFoundError: If PDF file doesn't exist
            Exception: If extraction fails
        """
        # Validate input file exists
        if not Path(self.pdf_path).exists():
            raise FileNotFoundError(f"PDF file not found: {self.pdf_path}")

        # Parse PDF
        text_blocks = self.parser.extract_text_blocks()

        # Normalize data
        dishes = self.normalizer.normalize_dishes(text_blocks)

        # Add dish IDs
        dishes = self.normalizer.add_dish_ids(dishes)

        # Clean descriptions
        dishes = self.normalizer.clean_descriptions(dishes)

        return dishes

    def save_to_json(self, dishes: List[Dict[str, Any]]) -> None:
        """
        Save dishes to JSON file.

        Args:
            dishes: List of dish dictionaries
        """
        # Ensure output directory exists
        output_dir = Path(self.output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)

        # Write JSON
        with open(self.output_path, 'w', encoding='utf-8') as f:
            json.dump(dishes, f, indent=2, ensure_ascii=False)

    def run(self) -> List[Dict[str, Any]]:
        """
        Run full extraction pipeline.

        Returns:
            List of extracted dishes

        Raises:
            Exception: If extraction or saving fails
        """
        print(f"Extracting menu from: {self.pdf_path}")

        # Extract dishes
        dishes = self.extract()

        print(f"Extracted {len(dishes)} dishes")

        # Save to JSON
        self.save_to_json(dishes)

        print(f"Saved to: {self.output_path}")

        return dishes


def main():
    """Main entry point for command-line usage."""
    import sys

    # Default paths
    pdf_path = "data/espn_bet.pdf"
    output_path = "output/menu_data.json"

    # Allow command-line arguments
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    if len(sys.argv) > 2:
        output_path = sys.argv[2]

    try:
        extractor = MenuExtractor(pdf_path, output_path)
        dishes = extractor.run()

        print(f"\nSuccess! Extracted {len(dishes)} dishes.")
        print(f"Output saved to: {output_path}")

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Extraction failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
