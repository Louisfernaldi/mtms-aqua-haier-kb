import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as pw:
        b = await pw.chromium.launch(executable_path=r"C:\Program Files\Google\Chrome\Application\chrome.exe")
        p = await b.new_page(viewport={"width": 1280, "height": 800})
        await p.goto("http://127.0.0.1:8765/index.html", wait_until="networkidle")
        await p.wait_for_timeout(800)
        print("index cards:", await p.evaluate("document.querySelectorAll('#ringkasan-brand .card').length"))
        await p.goto("http://127.0.0.1:8765/induksi.html", wait_until="networkidle"); await p.wait_for_timeout(800)
        print("induksi cards:", await p.evaluate("document.querySelectorAll('#konten-induksi .card').length"))
        await p.goto("http://127.0.0.1:8765/produk.html", wait_until="networkidle"); await p.wait_for_timeout(800)
        print("produk cards:", await p.evaluate("document.querySelectorAll('#konten-produk .card').length"))
        await p.goto("http://127.0.0.1:8765/rotasi.html", wait_until="networkidle"); await p.wait_for_timeout(800)
        print("rotasi cards:", await p.evaluate("document.querySelectorAll('#konten-rotasi .card').length"),
              "| svg charts:", await p.evaluate("document.querySelectorAll('svg').length"))
        await p.goto("http://127.0.0.1:8765/proses.html", wait_until="networkidle"); await p.wait_for_timeout(800)
        print("proses cards:", await p.evaluate("document.querySelectorAll('#konten-proses .card').length"))
        await p.goto("http://127.0.0.1:8765/galeri.html", wait_until="networkidle"); await p.wait_for_timeout(1500)
        print("galeri figures:", await p.evaluate("document.querySelectorAll('.gallery figure').length"),
              "| groups:", await p.evaluate("document.querySelectorAll('.sec').length"))
        await p.goto("http://127.0.0.1:8765/file.html", wait_until="networkidle"); await p.wait_for_timeout(800)
        print("file links:", await p.evaluate("document.querySelectorAll('.file-list a').length"))
        await p.evaluate("localStorage.setItem('ty-theme','dark')")
        await p.goto("http://127.0.0.1:8765/index.html", wait_until="networkidle")
        print("dark attr:", await p.evaluate("document.documentElement.getAttribute('data-theme')"))
        await p.evaluate("openSearch()"); await p.wait_for_timeout(400)
        await p.fill("#search-input", "garansi")
        await p.wait_for_timeout(400)
        n = await p.evaluate("document.querySelectorAll('#search-results .r').length")
        print("search 'garansi' results:", n)
        await p.goto("http://127.0.0.1:8765/galeri.html", wait_until="networkidle"); await p.wait_for_timeout(1200)
        await p.click(".gallery figure")
        await p.wait_for_timeout(300)
        print("lightbox open:", await p.evaluate("document.getElementById('lightbox').classList.contains('open')"))
        await b.close()

asyncio.run(main())