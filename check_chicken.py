import json

with open('output/menu_data.json', 'r', encoding='utf-8') as f:
    actual = json.load(f)

chicken = [d for d in actual if d['category'] == "AIN'T NO THING BUT A CHICKEN…" or 'CHICKEN' in d['category']]

print(f"Chicken category items: {len(chicken)}\n")
for i, d in enumerate(chicken, 1):
    print(f"{i}. {d['dish_name']} (price: {d['price']})")
