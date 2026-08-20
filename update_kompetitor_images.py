import json

# Load image map
with open('site/assets/kompetitor/image_map.json', encoding='utf-8') as f:
    image_map = json.load(f)

# Load kompetitor.json
with open('site/data/kompetitor.json', encoding='utf-8') as f:
    data = json.load(f)

# Add image field to models
updated = 0
for b in data['brands']:
    if b['brand'] == 'AQUA':
        continue
    for m in b['models']:
        key = f"{b['brand']}_{m['model']}"
        if key in image_map:
            m['image'] = image_map[key]
            updated += 1

print(f"Updated {updated} models with image paths")

# Save
with open('site/data/kompetitor.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("Done!")