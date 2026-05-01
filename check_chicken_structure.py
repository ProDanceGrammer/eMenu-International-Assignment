import sys
sys.path.insert(0, 'src')

from menu_extractor.parser import PDFParser

parser = PDFParser('data/espn_bet.pdf')
blocks = parser.extract_text_blocks()

# Find the chicken section
in_chicken = False
for i, block in enumerate(blocks):
    text = block.get('text', '').strip()

    if "AIN'T NO THING" in text or 'CHICKEN' in text and block.get('size', 0) > 12:
        in_chicken = True
        print(f"\n=== Found CHICKEN category at block {i} ===\n")

    if in_chicken and i >= 30 and i <= 80:
        x = block.get('x0', 0)
        size = block.get('size', 0)
        print(f"Block {i}: '{text}' (x={x:.1f}, size={size:.1f})")

    if in_chicken and 'SALADS' in text:
        break
