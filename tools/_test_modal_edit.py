import asyncio
from playwright.async_api import async_playwright
BASE = 'https://master.mtms-aqua-haier-kb.pages.dev'
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page()
        pg.on('console', lambda m: print('CONSOLE:', m.type, m.text))
        pg.on('pageerror', lambda e: print('PAGE ERROR:', e.message))
        await pg.goto(BASE + '/login', wait_until='networkidle')
        await pg.fill('#login-pass', 'aquaisthebest')
        await pg.click('#login-go')
        await pg.wait_for_timeout(2000)
        await pg.goto(BASE + '/produk.html', wait_until='networkidle')
        await pg.wait_for_timeout(5000)
        await b.close()
asyncio.run(main())