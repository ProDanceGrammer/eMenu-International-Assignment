import sys
sys.path.insert(0, 'src')
from menu_extractor.parser import PDFParser
from menu_extractor.normalizer import DataNormalizer

parser = PDFParser('data/espn_bet.pdf')
blocks = parser.extract_text_blocks()
normalizer = DataNormalizer()
normalizer._analyze_font_sizes(blocks)

# Manually trace through first 10 blocks
dishes = []
current_dish = None
previous_block = None
current_category = None
items_in_current_category = 0

for i, block in enumerate(blocks[:10]):
    text = block['text'].strip()

    if not text:
        continue

    print(f'\n=== Block {i}: "{text[:40]}..." (size={block.get("size", 0)}) ===')

    # Check should_stop_description
    if current_dish and normalizer.should_stop_description(block, previous_block):
        print(f'  -> STOP DESCRIPTION, saving dish: {current_dish["dish_name"]}')
        dishes.append(current_dish)
        current_dish = None

    # Check if section header
    if normalizer._is_section_header(text, block):
        print('  -> SECTION HEADER')
        if current_dish:
            dishes.append(current_dish)
            current_dish = None
        current_category = text
        previous_block = block
        continue

    # Check if price-only block
    if normalizer._contains_price(text) and len(text) <= 4:
        print(f'  -> PRICE-ONLY BLOCK')
        if current_dish and current_dish['price'] is None:
            print(f'     Attaching price to: {current_dish["dish_name"]}')
            current_dish['price'] = text
        else:
            print(f'     NOT attaching (current_dish={current_dish is not None}, price={current_dish["price"] if current_dish else "N/A"})')
        previous_block = block
        continue

    # Check if item without price
    if normalizer._is_item_without_price(text):
        print('  -> ITEM WITHOUT PRICE')
        if current_dish:
            print(f'     Saving previous dish: {current_dish["dish_name"]}')
            dishes.append(current_dish)
        current_dish = {
            'category': current_category,
            'dish_name': text,
            'price': None,
            'description': ''
        }
        print(f'     Created new dish: {text}')
        previous_block = block
        continue

    # Append as description
    if current_dish:
        print(f'  -> DESCRIPTION for: {current_dish["dish_name"]}')
        current_dish['description'] = normalizer._append_description(
            current_dish.get('description', ''),
            text
        )
        print(f'     Description now: "{current_dish["description"][:50]}..."')
    else:
        print('  -> SKIPPED (no current_dish)')

    previous_block = block

# Add last dish
if current_dish:
    dishes.append(current_dish)

print(f'\n\n=== FINAL RESULT: {len(dishes)} dishes ===')
for i, dish in enumerate(dishes):
    print(f'{i+1}. {dish["dish_name"]}')
    print(f'   Price: {dish["price"]}')
    print(f'   Description: "{dish["description"]}"')
