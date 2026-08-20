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

        # Click a Top Mount card
        await pg.click('.pk-card[data-model="AQR-355IM"]')
        await pg.wait_for_timeout(1000)

        # Check modal width on Detail tab
        modalWidth1 = await pg.eval_on_selector('.pk-modal-box', 'el => el.offsetWidth')
        print('Modal width (Detail tab):', modalWidth1)

        # Click comparison tab
        await pg.click('.pk-modal-tab[data-tab="comparison"]')
        await pg.wait_for_timeout(500)

        # Check modal width on Comparison tab
        modalWidth2 = await pg.eval_on_selector('.pk-modal-box', 'el => el.offsetWidth')
        print('Modal width (Comparison tab):', modalWidth2)

        # Check filmstrip card size
        cardWidth = await pg.eval_on_selector('.pk-film-card', 'el => el.offsetWidth')
        print('Film card width:', cardWidth)

        # Check images loaded
        imgSrc = await pg.eval_on_selector('.pk-film-img', 'el => el.src.substring(0, 50)')
        print('Image src (first 50):', imgSrc)

        await b.close()

asyncio.run(main())