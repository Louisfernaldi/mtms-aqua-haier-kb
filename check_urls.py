import json
with open('site/data/kompetitor.json', encoding='utf-8') as f:
    d = json.load(f)
for b in d['brands']:
    if b['brand'] in ['LG', 'SAMSUNG']:
        for m in b['models'][:2]:
            if 'source_url' in m:
                print(b['brand'], m['model'], m['source_url'])