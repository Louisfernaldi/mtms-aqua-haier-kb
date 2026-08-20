import json
with open('site/data/kompetitor.json', encoding='utf-8') as f:
    d = json.load(f)
for b in d['brands']:
    if b['brand'] != 'AQUA':
        for m in b['models']:
            if 'image' in m:
                print(b['brand'], m['model'], m['image'])