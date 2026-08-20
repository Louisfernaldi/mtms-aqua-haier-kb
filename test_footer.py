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

        # Click a Top Mount card
        await pg.click('.pk-card[data-model="AQR-355IM"]')
        await pg.wait_for_timeout(1000)

        # Check modal structure
        modalBox = await pg.eval_on_selector('.pk-modal-box', 'el => !!el')
        print('Modal box:', modalBox)

        modalBody = await pg.eval_on_selector('.pk-modal-body', 'el => !!el')
        print('Modal body:', modalBody)

        modalFooter = await pg.eval_on_selector('.pk-modal-footer', 'el => !!el')
        print('Modal footer:', modalFooter)

        # Check top tabs
        tabs = await pg.eval_on_selector_all('.pk-modal-tab', 'els => els.map(e => e.textContent.trim())')
        print('Top tabs:', tabs)

        # Check footer tabs
        footerTabs = await pg.eval_on_selector_all('.pk-modal-footer-tab', 'els => els.map(e => e.textContent.trim())')
        print('Footer tabs:', footerTabs)

        # Click comparison top tab
        await pg.click('.pk-modal-tab[data-tab="comparison"]')
        await pg.wait_for_timeout(1000)

        # Check filmstrip in top panel
        filmstrip1 = await pg.eval_on_selector('.pk-filmstrip', 'el => !!el')
        print('Filmstrip in top panel:', filmstrip1)

        # Click comparison footer tab
        await pg.click('.pk-modal-footer-tab[data-footer="comparison"]')
        await pg.wait_for_timeout(1000)

        # Check filmstrip in footer panel
        filmstrip2 = await pg.eval_on_selector('.pk-modal-footer-panel[data-footer="comparison"] .pk-filmstrip', 'el => !!el')
        print('Filmstrip in footer panel:', filmstrip2)

        # Click photos footer tab
        await pg.click('.pk-modal-footer-tab[data-footer="photos"]')
        await pg.wait_for_timeout(500)

        # Check photo gallery in footer
        gal = await pg.eval_on_selector('.pk-modal-footer-panel[data-footer="photos"] .pk-gal', 'el => !!el')
        print('Photo gallery in footer:', gal)

        galImg = await pg.eval_on_selector('.pk-modal-footer-panel[data-footer="photos"] .pk-gal-img', 'el => !!el')
        print('Gallery image in footer:', galImg)

        # Check image height
        if galImg:
            imgHeight = await pg.eval_on_selector('.pk-modal-footer-panel[data-footer="photos"] .pk-gal-img', 'el => el.naturalHeight + "x" + el.naturalWidth')
            print('Image natural size:', imgHeight)

        await b.close()

asyncio.run(main())