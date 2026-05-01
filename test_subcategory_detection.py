import sys
sys.path.insert(0, 'src')

from menu_extractor.parser import PDFParser

parser = PDFParser('data/espn_bet.pdf')
blocks = parser.extract_text_blocks()

# Simulate the subcategory detection for LOADED MAC
loaded_mac_block = None
for i, block in enumerate(blocks):
    text = block.get('text', '').strip()
    if text == 'LOADED MAC':
        loaded_mac_block = (i, block)
        break

if loaded_mac_block:
    i, block = loaded_mac_block
    text = block.get('text', '').strip()
    current_y = block.get('top', 0)
    current_x = block.get('x0', 0)
    current_size = block.get('size', 0)

    print(f"Block {i}: '{text}'")
    print(f"  Size: {current_size:.2f}, X: {current_x:.2f}, Y: {current_y:.2f}")
    print(f"  Is upper: {text.isupper()}")
    print(f"  Has price: {'$' in text}")
    print(f"  Word count: {len(text.split())}")
    print()

    print("Looking ahead for subcategory detection:")
    for j in range(i + 1, min(i + 15, len(blocks))):
        next_block = blocks[j]
        next_text = next_block['text'].strip()
        next_y = next_block.get('top', 0)
        next_x = next_block.get('x0', 0)
        next_size = next_block.get('size', 0)

        # Skip blocks on the same line
        if abs(next_y - current_y) < 3:
            print(f"  Block {j}: '{next_text}' - SAME LINE, skipping")
            continue

        # Check if in same column
        if abs(next_x - current_x) < 30:
            print(f"  Block {j}: '{next_text}'")
            print(f"    Size: {next_size:.2f}, same column: True")
            print(f"    Size comparison: next={next_size:.2f} vs current={current_size:.2f}")
            print(f"    next < current: {next_size < current_size}")
            print(f"    Has price: {'$' in next_text}")

            if next_size < current_size:
                print(f"    -> Would be detected as SUBCATEGORY")
                break
            elif next_size >= current_size and '$' not in next_text:
                print(f"    -> Same/larger size, no price - STOP looking")
                break
