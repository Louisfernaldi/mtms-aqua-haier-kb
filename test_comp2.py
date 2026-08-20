import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=False)
        pg = await b.new_page()
        pg.on('console', lambda m: print('CONSOLE:', m.type, m.text) if m.type == 'error' else None)
        pg.on('pageerror', lambda e: print('PAGE ERROR:', e.message))

        # Login
        await pg.goto('https://master.mtms-aqua-haier-kb.pages.dev/login', wait_until='domcontentloaded', timeout=15000)
        await pg.fill('#login-pass', 'aquaisthebest')
        await pg.click('#login-go')
        await pg.wait_for_load_state('domcontentloaded', timeout=15000)
        await pg.wait_for_timeout(2000)

        # Go to produk
        await pg.goto('https://master.mtms-aqua-haier-kb.pages.dev/produk.html', wait_until='domcontentloaded', timeout=15000)
        await pg.wait_for_timeout(3000)

        # Click a Top Mount card - AQR-355IM (TM category)
        await pg.click('.pk-card[data-model="AQR-355IM"]')
        await pg.wait_for_timeout(1000)

        # Click comparison tab
        await pg.click('.pk-modal-tab[data-tab="comparison"]')
        await pg.wait_for_timeout(2000)

        # Check comparison table
        compTable = await pg.eval_on_selector('.pk-comp-table', 'el => !!el')
        print('Comparison table:', compTable)

        if compTable:
            rows = await pg.eval_on_selector_all('.pk-comp-table tbody tr', 'els => els.map(e => Array.from(e.querySelectorAll("td")).map(c => c.textContent.trim()))')
            print('Competitor rows:', rows)

        await b.close()

asyncio.run(main())