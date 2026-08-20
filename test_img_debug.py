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

        await pg.goto('https://master.mtms-aqua-haier-kb.pages.dev/produk.html', wait_until='domcontentloaded', timeout=15000)
        await pg.wait_for_timeout(3000)

        await pg.click('.pk-card[data-model="AQR-355IM"]')
        await pg.wait_for_timeout(1000)
        await pg.click('.pk-modal-tab[data-tab="comparison"]')
        await pg.wait_for_timeout(1000)

        await pg.screenshot(path='comparison_debug.png', full_page=True)
        print('Screenshot saved')

        srcs = await pg.eval_on_selector_all('.pk-film-img', 'els => els.map(e => e.src.substring(0, 80))')
        for i, s in enumerate(srcs):
            print(f'Card {i}: {s}')

        await b.close()

asyncio.run(main())