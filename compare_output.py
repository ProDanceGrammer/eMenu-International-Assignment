import json
from collections import Counter

with open('output/menu_data.json', 'r', encoding='utf-8') as f:
    actual = json.load(f)

with open('output/expected_menu_data.json', 'r', encoding='utf-8') as f:
    expected = json.load(f)

print(f'Total: {len(actual)}/{len(expected)} (need {len(expected) - len(actual)} more)')
print()

actual_cats = Counter([d['category'] for d in actual])
expected_cats = Counter([d['category'] for d in expected])

print('Category comparison:')
for cat in sorted(set(list(actual_cats.keys()) + list(expected_cats.keys()))):
    a = actual_cats.get(cat, 0)
    e = expected_cats.get(cat, 0)
    status = 'OK' if a == e else f'({e - a:+d})'
    print(f'  {cat}: {a}/{e} {status}')
print()

# Check MAIN EVENT details
print('MAIN EVENT actual:')
main_actual = [d for d in actual if d['category'] == 'MAIN EVENT']
for d in main_actual:
    print(f'  - {d["dish_name"]} (price: {d["price"]})')
print()

print('MAIN EVENT expected:')
main_expected = [d for d in expected if d['category'] == 'MAIN EVENT']
for d in main_expected:
    print(f'  - {d["dish_name"]} (price: {d["price"]})')
print()

# Check WINES details
print('WINES actual:')
wines_actual = [d for d in actual if d['category'] == 'WINES']
for d in wines_actual:
    print(f'  - {d["dish_name"]}')
print()

print('WINES expected:')
wines_expected = [d for d in expected if d['category'] == 'WINES']
for d in wines_expected:
    print(f'  - {d["dish_name"]}')
