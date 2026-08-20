import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=False)
        pg = await b.new_page()
        pg.on('console', lambda m: print('CONSOLE:', m.type, m.text))
        pg.on('pageerror', lambda e: print('PAGE ERROR:', e.message))

        await pg.goto('https://master.mtms-aqua-haier-kb.pages.dev/login', wait_until='domcontentloaded', timeout=15000)
        await pg.fill('#login-pass', 'aquaisthebest')
        await pg.click('#login-go')
        await pg.wait_for_load_state('domcontentloaded', timeout=15000)
        await pg.wait_for_timeout(2000)

        await pg.goto('https://master.mtms-aqua-haier-kb.pages.dev/produk.html', wait_until='domcontentloaded', timeout=15000)
        await pg.wait_for_timeout(10000)

        # Check if konten-katalog has children
        children = await pg.evaluate('''() => {
            const host = document.getElementById('konten-katalog');
            if (!host) return 'NO HOST';
            return Array.from(host.children).map(c => c.tagName + (c.className ? '.' + c.className : ''));
        }''')
        print('Konten-katalog children:', children)

        # Check if renderKatalog function exists
        renderExists = await pg.evaluate('typeof renderKatalog')
        print('renderKatalog type:', renderExists)

        await b.close()

asyncio.run(main())