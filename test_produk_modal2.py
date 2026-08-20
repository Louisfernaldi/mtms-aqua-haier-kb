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
        await pg.wait_for_timeout(5000)

        # Check cards
        cards = await pg.eval_on_selector_all('.pk-card', 'els => els.length')
        print('Cards:', cards)

        # Check modal structure
        modal = await pg.eval_on_selector('.pk-modal', 'el => !!el')
        print('Modal:', modal)

        modalBody = await pg.eval_on_selector('.pk-modal-body', 'el => !!el')
        print('Modal body:', modalBody)

        modalFooter = await pg.eval_on_selector('.pk-modal-footer', 'el => !!el')
        print('Modal footer:', modalFooter)

        # Check no top tabs
        tabs = await pg.eval_on_selector_all('.pk-modal-tab', 'els => els.map(e => e.textContent.trim())')
        print('Top tabs:', tabs)

        # Check no footer tabs
        footerTabs = await pg.eval_on_selector_all('.pk-modal-footer-tab', 'els => els.map(e => e.textContent.trim())')
        print('Footer tabs:', footerTabs)

        # Click first card
        if cards > 0:
            await pg.click('.pk-card:first-child')
            await pg.wait_for_timeout(1000)

            # Check modal opened
            modalOpen = await pg.eval_on_selector('.pk-modal.open', 'el => !!el')
            print('Modal open:', modalOpen)

            # Check footer has photo gallery
            gal = await pg.eval_on_selector('.pk-modal-footer .pk-gal', 'el => !!el')
            print('Photo gallery in footer:', gal)

            galImg = await pg.eval_on_selector('.pk-modal-footer .pk-gal-img', 'el => !!el')
            print('Gallery image in footer:', galImg)

        await b.close()

asyncio.run(main())