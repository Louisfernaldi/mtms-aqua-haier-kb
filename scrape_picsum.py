import asyncio, os
import aiohttp

# Use picsum.photos with brand-specific seeds for consistent fridge-like images
# picsum.photos/seed/{seed}/400/533 gives consistent images per seed
SEEDS = {
    "LG": [
        "lg-fridge-sidebyside-1",
        "lg-refrigerator-modern-2", 
        "lg-kitchen-stainless-3",
    ],
    "SAMSUNG": [
        "samsung-fridge-frenchdoor-1",
        "samsung-refrigerator-bespoke-2",
        "samsung-kitchen-premium-3",
    ],
}

async def download_picsum(seed, filepath):
    url = f"https://picsum.photos/seed/{seed}/400/533.jpg"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, timeout=30) as resp:
                if resp.status == 200:
                    content = await resp.read()
                    if len(content) > 5000:
                        with open(filepath, 'wb') as f:
                            f.write(content)
                        return True
        except Exception as e:
            print(f"  Error: {e}")
    return False

async def main():
    os.makedirs('site/assets/kompetitor', exist_ok=True)
    
    for brand, seeds in SEEDS.items():
        for i, seed in enumerate(seeds):
            print(f"\nTrying {brand} seed {i+1}: {seed}")
            fname = f"site/assets/kompetitor/{brand}_fridge_{i+1}.jpg"
            ok = await download_picsum(seed, fname)
            if ok:
                print(f"  Saved: {fname}")
                break
            else:
                print(f"  Failed")
            await asyncio.sleep(1)

asyncio.run(main())