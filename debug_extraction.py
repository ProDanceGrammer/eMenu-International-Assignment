"""
Debug script to inspect raw PDF extraction
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from menu_extractor.parser import PDFParser

parser = PDFParser("data/espn_bet.pdf")
blocks = parser.extract_text_blocks()

print("First 30 text blocks:")
print("=" * 80)

for i, block in enumerate(blocks[:30], 1):
    print(f"\n{i}. [{block.get('page', '?')}] x0={block['x0']:.1f}, top={block['top']:.1f}")
    print(f"   Text: {block['text'][:100]}")
