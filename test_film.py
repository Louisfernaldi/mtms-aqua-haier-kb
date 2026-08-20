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

        # Click a Bottom Mount card to test comparison
        await pg.click('.pk-card[data-model="AQR-350RBM"]')
        await pg.wait_for_timeout(1000)

        # Check tabs exist
        tabs = await pg.eval_on_selector_all('.pk-modal-tab', 'els => els.map(e => e.textContent.trim())')
        print('Tabs:', tabs)

        # Click comparison tab
        await pg.click('.pk-modal-tab[data-tab="comparison"]')
        await pg.wait_for_timeout(2000)

        # Check filmstrip exists
        filmstrip = await pg.eval_on_selector('.pk-filmstrip', 'el => !!el')
        print('Filmstrip:', filmstrip)

        if filmstrip:
            cards = await pg.eval_on_selector_all('.pk-film-card', 'els => els.map(e => e.querySelector(".pk-film-brand")?.textContent.trim())')
            print('Film cards (brands):', cards)
            
            # Check indicators
            dots = await pg.eval_on_selector_all('.pk-film-dot', 'els => els.length')
            print('Indicator dots:', dots)
            
            # Test keyboard nav
            await pg.keyboard.press('ArrowRight')
            await pg.wait_for_timeout(500)
            active = await pg.eval_on_selector('.pk-film-dot.active', 'el => el.dataset.idx')
            print('After ArrowRight, active idx:', active)

        await b.close()

asyncio.run(main())