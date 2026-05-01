import pdfplumber
import sys
sys.path.insert(0, 'src')

from menu_extractor.parser import PDFParser

parser = PDFParser('data/espn_bet.pdf')
blocks = parser.extract_text_blocks()

# Find blocks around LOADED MAC
in_main_event = False
for i, block in enumerate(blocks):
    text = block.get('text', '').strip()

    if 'MAIN EVENT' in text:
        in_main_event = True
        print(f"\n=== Found MAIN EVENT at block {i} ===")

    if in_main_event:
        if 'LOADED MAC' in text or 'MAC DINNER' in text or 'NASHVILLE' in text or 'SMOKED' in text:
            print(f"\nBlock {i}:")
            print(f"  Text: {text}")
            print(f"  Size: {block.get('size', 0)}")
            print(f"  X: {block.get('x0', 0)}")
            print(f"  Y: {block.get('top', 0)}")

    if in_main_event and 'SIDES' in text:
        print(f"\n=== SIDES category at block {i}, stopping ===")
        break
