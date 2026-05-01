import json

with open('output/before_split.json', 'r', encoding='utf-8') as f:
    before = json.load(f)

print(f'Before split: {len(before)} dishes')
print()

# Check MAIN EVENT
main_event = [d for d in before if d['category'] == 'MAIN EVENT']
print(f'MAIN EVENT before split: {len(main_event)} items')
for d in main_event:
    print(f'  - {d["dish_name"]} (price: {d["price"]})')
print()

# Check WINES
wines = [d for d in before if d['category'] == 'WINES']
print(f'WINES before split: {len(wines)} items')
for d in wines:
    print(f'  - {d["dish_name"]} (price: {d["price"]})')
