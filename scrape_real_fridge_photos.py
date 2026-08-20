import json, asyncio, os
from playwright.async_api import async_playwright

async def get_product_image(url, brand):
    """Extract actual product image from manufacturer page"""
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True)
        pg = await b.new_page()
        try:
            await pg.goto(url, wait_until='networkidle', timeout=30000)
            await pg.wait_for_timeout(2000)
            
            # Strategy 1: og:image
            og = None
            try:
                og = await pg.eval_on_selector('meta[property="og:image"]', 'el => el.content')
            except:
                pass
            if og and ('jpg' in og or 'png' in og or 'webp' in og):
                await b.close()
                return og
            
            # Strategy 2: Look for product gallery images
            # Common patterns for fridge product images
            imgs = await pg.eval_on_selector_all('img', '''els => els
                .filter(e => e.naturalWidth > 300 && e.naturalHeight > 300)
                .filter(e => e.src && (e.src.includes('product') || e.src.includes('gallery') || e.src.includes('hero') || e.src.includes('main') || e.src.includes('fridge') || e.src.includes('refrigerator')))
                .map(e => e.src)''')
            if imgs and len(imgs) > 0:
                await b.close()
                return imgs[0]
            
            # Strategy 3: Any large image
            imgs2 = await pg.eval_on_selector_all('img', '''els => els
                .filter(e => e.naturalWidth > 400 && e.naturalHeight > 300)
                .map(e => e.src)''')
            if imgs2 and len(imgs2) > 0:
                await b.close()
                return imgs2[0]
                
        except Exception as e:
            print(f"  Error: {e}")
        await b.close()
    return None

async def download_image(url, filepath):
    """Download image to local file"""
    import aiohttp
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, timeout=30) as resp:
                if resp.status == 200:
                    content = await resp.read()
                    with open(filepath, 'wb') as f:
                        f.write(content)
                    return True
        except Exception as e:
            print(f"  Download failed: {e}")
    return False

async def main():
    with open('site/data/kompetitor.json', encoding='utf-8') as f:
        data = json.load(f)

    # Pick one model per brand per category for photo
    target_models = {}
    for b in data['brands']:
        if b['brand'] == 'AQUA':
            continue
        for m in b['models']:
            key = f"{b['brand']}_{m.get('cat', m.get('subcat', ''))}"
            if key not in target_models and 'source_url' in m and m['source_url']:
                target_models[key] = (b['brand'], m['model'], m['source_url'], m.get('cat', m.get('subcat', '')))

    print(f"Target models: {len(target_models)}")
    for k, v in target_models.items():
        print(f"  {k}: {v[1]} ({v[3]})")

    # Scrape images
    os.makedirs('site/assets/kompetitor', exist_ok=True)
    results = {}
    
    for key, (brand, model, url, cat) in target_models.items():
        print(f"\nScraping {brand} {model} ({cat})...")
        img_url = await get_product_image(url, brand)
        if img_url:
            print(f"  Found: {img_url[:80]}")
            # Download
            ext = '.jpg'
            if 'webp' in img_url: ext = '.webp'
            elif 'png' in img_url: ext = '.png'
            fname = f"site/assets/kompetitor/{brand}_{model}{ext}"
            ok = await download_image(img_url, fname)
            if ok:
                results[f"{brand}_{model}"] = f"assets/kompetitor/{brand}_{model}{ext}"
                print(f"  Saved to {fname}")
            else:
                print(f"  Download failed")
        else:
            print(f"  No image found")
        await asyncio.sleep(2)

    # Save mapping
    with open('site/assets/kompetitor/image_map.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    print(f"\nDone. Got {len(results)} images.")

asyncio.run(main())