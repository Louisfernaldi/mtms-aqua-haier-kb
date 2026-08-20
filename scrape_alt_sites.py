import json, asyncio, os, re
from playwright.async_api import async_playwright

# Try different regional sites for LG/Samsung
ALTERNATIVE_URLS = {
    "LG": {
        "GC-L257CQEL": [
            "https://www.lg.com/us/refrigerators/lg-GC-L257CQEL",
            "https://www.lg.com/global/refrigerators/lg-GC-L257CQEL",
        ],
        "GC-V22FFQMB": [
            "https://www.lg.com/us/refrigerators/lg-GC-V22FFQMB",
            "https://www.lg.com/global/refrigerators/lg-GC-V22FFQMB",
        ],
    },
    "SAMSUNG": {
        "RB30N4050B1_SE": [
            "https://www.samsung.com/us/refrigerators/rb30n4050b1/",
            "https://www.samsung.com/global/galaxy/what-is/rb30n4050b1/",
        ],
        "RF48A4000B4_SE": [
            "https://www.samsung.com/us/refrigerators/rf48a4000b4/",
        ],
    }
}

async def try_get_image(url, brand):
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True)
        pg = await b.new_page()
        # Set realistic headers
        await pg.set_extra_http_headers({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        })
        try:
            await pg.goto(url, wait_until='networkidle', timeout=30000)
            await pg.wait_for_timeout(3000)
            
            # Try multiple strategies
            strategies = [
                'meta[property="og:image"]',
                'meta[name="twitter:image"]',
                'img[data-testid="product-image"]',
                'img.product-image',
                'img[class*="hero"]',
                'img[class*="main"]',
                'img[class*="gallery"]',
                'picture img',
            ]
            
            for sel in strategies:
                try:
                    src = await pg.eval_on_selector(sel, 'el => el.src || el.content')
                    if src and ('jpg' in src or 'png' in src or 'webp' in src) and len(src) > 10:
                        await b.close()
                        return src
                except:
                    pass
            
            # Fallback: any large image
            imgs = await pg.eval_on_selector_all('img', '''els => els
                .filter(e => e.naturalWidth > 400 && e.naturalHeight > 300)
                .map(e => e.src)''')
            if imgs:
                await b.close()
                return imgs[0]
                
        except Exception as e:
            print(f"  Error {url}: {e}")
        await b.close()
    return None

async def download_image(url, filepath):
    import aiohttp
    async with aiohttp.ClientSession() as session:
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            async with session.get(url, headers=headers, timeout=30) as resp:
                if resp.status == 200:
                    content = await resp.read()
                    with open(filepath, 'wb') as f:
                        f.write(content)
                    return True
        except Exception as e:
            print(f"  Download failed: {e}")
    return False

async def main():
    os.makedirs('site/assets/kompetitor', exist_ok=True)
    
    for brand, models in ALTERNATIVE_URLS.items():
        for model, urls in models.items():
            print(f"\nTrying {brand} {model}...")
            for url in urls:
                print(f"  Trying: {url}")
                img_url = await try_get_image(url, brand)
                if img_url:
                    print(f"  Found: {img_url[:80]}")
                    ext = '.jpg'
                    if 'webp' in img_url: ext = '.webp'
                    elif 'png' in img_url: ext = '.png'
                    fname = f"site/assets/kompetitor/{brand}_{model}{ext}"
                    ok = await download_image(img_url, fname)
                    if ok:
                        print(f"  Saved: {fname}")
                        break
                else:
                    print(f"  No image found")
                await asyncio.sleep(2)
            else:
                print(f"  ALL URLS FAILED for {brand} {model}")

asyncio.run(main())