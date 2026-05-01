import json

with open('output/menu_data.json', 'r', encoding='utf-8') as f:
    actual = json.load(f)

with open('output/expected_menu_data.json', 'r', encoding='utf-8') as f:
    expected = json.load(f)

print("Checking for mismatches:\n")
mismatches = []
for i, (actual_dish, expected_dish) in enumerate(zip(actual, expected)):
    if actual_dish['dish_name'] != expected_dish['dish_name']:
        mismatches.append((i, actual_dish['dish_name'], expected_dish['dish_name']))

print(f"Found {len(mismatches)} dish_name mismatches:\n")
for i, actual_name, expected_name in mismatches[:10]:
    print(f"Dish {i}:")
    print(f"  Actual:   '{actual_name}'")
    print(f"  Expected: '{expected_name}'")
    print()
