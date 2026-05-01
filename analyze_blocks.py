import sys
sys.path.insert(0, 'src')

from menu_extractor.parser import PDFParser

parser = PDFParser('data/espn_bet.pdf')
blocks = parser.extract_text_blocks()

# Find the blocks for LOADED MAC, NASHVILLE MAC, SMOKED MAC
print("=== Blocks in MAIN EVENT section ===\n")
in_main = False
for i, block in enumerate(blocks):
    text = block.get('text', '').strip()

    if 'MAIN EVENT' in text:
        in_main = True

    if in_main and (i >= 112 and i <= 123):
        has_price = '$' in text
        print(f"Block {i}: '{text}'")
        print(f"  Size: {block.get('size', 0):.2f}, X: {block.get('x0', 0):.2f}")
        print(f"  Has price: {has_price}")
        print(f"  Is upper: {text.isupper()}")
        print(f"  Word count: {len(text.split())}")
        print()

    if in_main and 'SIDES' in text:
        break
