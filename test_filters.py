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

        # Test TM filter
        await pg.select_option('#comp-category', 'TM')
        await pg.wait_for_timeout(2000)
        cards = await pg.eval_on_selector_all('.pk-film-card', 'els => els.map(e => e.querySelector(".pk-film-brand")?.textContent.trim())')
        print('TM filter cards:', cards)

        srcs = await pg.eval_on_selector_all('.pk-film-img', 'els => els.map(e => e.src.substring(0, 80))')
        for i, s in enumerate(srcs):
            print(f'Card {i}: {s}')

        # Test BM filter
        await pg.select_option('#comp-category', 'BM')
        await pg.wait_for_timeout(2000)
        cards = await pg.eval_on_selector_all('.pk-film-card', 'els => els.map(e => e.querySelector(".pk-film-brand")?.textContent.trim())')
        print('BM filter cards:', cards)

        srcs = await pg.eval_on_selector_all('.pk-film-img', 'els => els.map(e => e.src.substring(0, 80))')
        for i, s in enumerate(srcs):
            print(f'Card {i}: {s}')

        await b.close()

asyncio.run(main())