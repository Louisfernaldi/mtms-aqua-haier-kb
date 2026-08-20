import json

# Load kompetitor.json
with open('site/data/kompetitor.json', encoding='utf-8') as f:
    data = json.load(f)

# Map LG/Samsung models to the downloaded images
# Use the first downloaded image for all LG models, first for all Samsung models
image_map = {
    "LG": "assets/kompetitor/LG_fridge_1.jpg",
    "SAMSUNG": "assets/kompetitor/SAMSUNG_fridge_1.jpg",
}

updated = 0
for b in data['brands']:
    if b['brand'] in ['LG', 'SAMSUNG']:
        for m in b['models']:
            if 'image' not in m:
                m['image'] = image_map[b['brand']]
                updated += 1

print(f"Updated {updated} models with fridge images")

# Save
with open('site/data/kompetitor.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("Done!")