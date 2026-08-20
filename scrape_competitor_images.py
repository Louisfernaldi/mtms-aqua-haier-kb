import json, asyncio
from playwright.async_api import async_playwright

async def scrape_og_image(url):
    """Fetch page and extract og:image or first large product image"""
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True)
        pg = await b.new_page()
        try:
            await pg.goto(url, wait_until='domcontentloaded', timeout=15000)
            # Try og:image first
            og = None
            try:
                og = await pg.eval_on_selector('meta[property="og:image"]', 'el => el.content')
            except:
                pass
            if og:
                await b.close()
                return og
            # Try twitter:image
            tw = None
            try:
                tw = await pg.eval_on_selector('meta[name="twitter:image"]', 'el => el.content')
            except:
                pass
            if tw:
                await b.close()
                return tw
            # Try first large img
            imgs = await pg.eval_on_selector_all('img', 'els => els.filter(e => e.naturalWidth > 200 && e.naturalHeight > 200).map(e => e.src)')
            if imgs and len(imgs) > 0:
                await b.close()
                return imgs[0]
        except Exception as e:
            pass
        await b.close()
    return None

async def main():
    with open('site/data/kompetitor.json', encoding='utf-8') as f:
        data = json.load(f)

    # Collect unique models with source_url
    models_to_scrape = []
    for b in data['brands']:
        if b['brand'] == 'AQUA':
            continue
        for m in b['models']:
            if 'source_url' in m and m['source_url']:
                models_to_scrape.append((b['brand'], m['model'], m['source_url']))

    print(f"Total models to scrape: {len(models_to_scrape)}")

    # Scrape in batches
    results = {}
    for brand, model, url in models_to_scrape[:10]:  # test first 10
        print(f"Scraping {brand} {model}...")
        img = await scrape_og_image(url)
        if img:
            results[f"{brand}_{model}"] = img
            print(f"  -> {img[:80]}")
        else:
            print(f"  -> FAILED")
        await asyncio.sleep(1)

    print("\nResults:")
    for k, v in results.items():
        print(f"{k}: {v}")

    # Save results
    with open('scraped_images.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)

asyncio.run(main())