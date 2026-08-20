import json, asyncio, os, re
import aiohttp

# Use Unsplash Source API for fridge photos per brand
# Format: https://source.unsplash.com/featured/400x533/?fridge,lg,refrigerator
UNSPLASH_QUERIES = {
    "LG": [
        "fridge,lg,refrigerator,modern,kitchen",
        "refrigerator,lg,side-by-side,modern",
        "kitchen,lg,fridge,stainless,steel",
    ],
    "SAMSUNG": [
        "fridge,samsung,refrigerator,modern,kitchen",
        "refrigerator,samsung,french-door,modern",
        "kitchen,samsung,fridge,bespoke,design",
    ],
}

async def download_unsplash(query, filepath):
    """Download from Unsplash Source API"""
    url = f"https://source.unsplash.com/featured/400x533/?{query}"
    async with aiohttp.ClientSession() as session:
        try:
            # Follow redirects
            async with session.get(url, allow_redirects=True, timeout=30) as resp:
                if resp.status == 200:
                    content = await resp.read()
                    if len(content) > 10000:  # Valid image
                        with open(filepath, 'wb') as f:
                            f.write(content)
                        return True
        except Exception as e:
            print(f"  Error: {e}")
    return False

async def main():
    os.makedirs('site/assets/kompetitor', exist_ok=True)
    
    for brand, queries in UNSPLASH_QUERIES.items():
        for i, query in enumerate(queries):
            print(f"\nTrying {brand} query {i+1}: {query}")
            fname = f"site/assets/kompetitor/{brand}_placeholder_{i+1}.jpg"
            ok = await download_unsplash(query, fname)
            if ok:
                print(f"  Saved: {fname}")
                break
            else:
                print(f"  Failed")
            await asyncio.sleep(2)

asyncio.run(main())