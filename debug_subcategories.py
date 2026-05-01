import sys
sys.path.insert(0, 'src')

from menu_extractor.parser import PDFParser
from menu_extractor.normalizer import DataNormalizer

parser = PDFParser('data/espn_bet.pdf')
blocks = parser.extract_text_blocks()

# Patch the normalizer to print subcategory detection
original_normalize = DataNormalizer.normalize_dishes

def debug_normalize(self, text_blocks):
    # Store original subcategories setter
    original_dict = {}

    class DebugDict(dict):
        def __setitem__(self, key, value):
            print(f"  Setting subcategory: {value} at x={key}")
            super().__setitem__(key, value)

    self.subcategories = DebugDict()
    return original_normalize(self, text_blocks)

DataNormalizer.normalize_dishes = debug_normalize

normalizer = DataNormalizer()
print("=== Tracking subcategory assignments ===\n")
dishes = normalizer.normalize_dishes(blocks)

print("\n=== MAIN EVENT dishes ===")
main_event = [d for d in dishes if d['category'] == 'MAIN EVENT']
for d in main_event:
    print(f'  - {d["dish_name"]} (price: {d["price"]})')
