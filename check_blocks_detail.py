import sys
sys.path.insert(0, 'src')

from menu_extractor.parser import PDFParser

parser = PDFParser('data/espn_bet.pdf')
blocks = parser.extract_text_blocks()

# Find blocks around LOADED MAC with more context
in_main_event = False
for i, block in enumerate(blocks):
    text = block.get('text', '').strip()

    if 'MAIN EVENT' in text:
        in_main_event = True
        print(f"\n=== Found MAIN EVENT at block {i} ===")

    if in_main_event and i >= 112 and i <= 125:
        print(f"\nBlock {i}:")
        print(f"  Text: '{text}'")
        print(f"  Size: {block.get('size', 0)}")
        print(f"  X: {block.get('x0', 0)}")
        print(f"  Y: {block.get('top', 0)}")

        # Check if it contains a price
        if '$' in text:
            print(f"  ** Contains price **")

    if in_main_event and 'SIDES' in text:
        break
