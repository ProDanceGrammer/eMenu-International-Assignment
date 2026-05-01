import sys
sys.path.insert(0, 'src')

from menu_extractor.normalizer import DataNormalizer

normalizer = DataNormalizer()

test_items = [
    "LOADED MAC",
    "NASHVILLE MAC",
    "SMOKED MAC",
    "MAC DINNER �ORIGINAL� MAC"
]

print("=== Testing _is_item_without_price ===\n")
for item in test_items:
    result = normalizer._is_item_without_price(item)
    print(f"'{item}': {result}")
