import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=False)
        pg = await b.new_page()
        pg.on('console', lambda m: print('CONSOLE:', m.type, m.text) if m.type == 'error' else None)
        pg.on('pageerror', lambda e: print('PAGE ERROR:', e.message))

        await pg.goto('https://master.mtms-aqua-haier-kb.pages.dev/login', wait_until='domcontentloaded', timeout=15000)
        await pg.fill('#login-pass', 'aquaisthebest')
        await pg.click('#login-go')
        await pg.wait_for_load_state('domcontentloaded', timeout=15000)
        await pg.wait_for_timeout(2000)

        await pg.goto('https://master.mtms-aqua-haier-kb.pages.dev/kompetitor.html', wait_until='domcontentloaded', timeout=15000)
        await pg.wait_for_timeout(5000)

        # Check categories
        sections = await pg.eval_on_selector_all('.comp-category-section', 'els => els.length')
        print('Category sections:', sections)

        # Check table rows
        rows = await pg.eval_on_selector_all('.comp-full-table tbody tr', 'els => els.length')
        print('Table rows:', rows)

        # Check first row cells
        cells = await pg.eval_on_selector_all('.comp-full-table tbody tr:first-child td', 'els => els.map(e => e.querySelector(".comp-model-name")?.textContent.trim() || e.textContent.trim().substring(0,30))')
        print('First row cells:', cells)

        # Check images
        imgs = await pg.eval_on_selector_all('.comp-thumb', 'els => els.map(e => e.src.substring(0, 80))')
        for i, s in enumerate(imgs[:6]):
            print(f'Img {i}: {s}')

        await b.close()

asyncio.run(main())