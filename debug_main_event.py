import sys
sys.path.insert(0, 'src')

from menu_extractor.parser import PDFParser
from menu_extractor.normalizer import DataNormalizer

parser = PDFParser('data/espn_bet.pdf')
blocks = parser.extract_text_blocks()

normalizer = DataNormalizer()
dishes = normalizer.normalize_dishes(blocks)

# Check MAIN EVENT before filtering
main_event = [d for d in dishes if d['category'] == 'MAIN EVENT']
print(f'MAIN EVENT after normalize_dishes: {len(main_event)} items')
for d in main_event:
    print(f'  - {d["dish_name"]} (price: {d["price"]})')
print()

# Apply filtering
dishes = normalizer.filter_non_menu_items(dishes)
main_event = [d for d in dishes if d['category'] == 'MAIN EVENT']
print(f'MAIN EVENT after filter_non_menu_items: {len(main_event)} items')
for d in main_event:
    print(f'  - {d["dish_name"]} (price: {d["price"]})')
