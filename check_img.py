import json
with open('site/data/kompetitor.json', encoding='utf-8') as f:
    d = json.load(f)

# Check if any models have image field
for b in d['brands']:
    if b['brand'] != 'AQUA':
        for m in b['models'][:3]:
            has_img = 'image' in m or 'foto' in m or 'photo' in m
            print(b['brand'], m['model'], 'has_image=', has_img, 'keys=', list(m.keys()))