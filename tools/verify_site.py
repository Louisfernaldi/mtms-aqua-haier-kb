import asyncio, json, os, sys
from playwright.async_api import async_playwright

BASE = "http://127.0.0.1:8765/"
PAGES = ["index.html", "induksi.html", "produk.html", "rotasi.html", "proses.html", "galeri.html", "file.html"]
EVID = r"D:\AI\projects\mtms-aqua-haier-kb\tools\evidence"
os.makedirs(EVID, exist_ok=True)

async def main():
    results = {}
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(executable_path=r"C:\Program Files\Google\Chrome\Application\chrome.exe")
        for page_name in PAGES:
            page = await browser.new_page(viewport={"width": 390, "height": 844})
            errors = []
            page.on("console", lambda m, pn=page_name: errors.append(f"console-{m.type}: {m.text}") if m.type in ("error",) else None)
            page.on("pageerror", lambda e, pn=page_name: errors.append(f"pageerror: {e}"))
            await page.goto(BASE + page_name, wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(1200)
            hscroll = await page.evaluate("document.documentElement.scrollWidth > document.documentElement.clientWidth")
            await page.screenshot(path=os.path.join(EVID, f"{page_name.replace('.html','')}_390.png"), full_page=False)
            await page.close()
            results[page_name] = {"errors390": errors, "hscroll390": hscroll}

        page = await browser.new_page(viewport={"width": 1280, "height": 800})
        errs_desktop = []
        page.on("console", lambda m: errs_desktop.append(f"console-{m.type}: {m.text}") if m.type in ("error",) else None)
        page.on("pageerror", lambda e: errs_desktop.append(f"pageerror: {e}"))
        for page_name in PAGES:
            await page.goto(BASE + page_name, wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(1000)
            hscroll = await page.evaluate("document.documentElement.scrollWidth > document.documentElement.clientWidth")
            results[page_name]["hscroll1280"] = hscroll
        await page.screenshot(path=os.path.join(EVID, "index_1280.png"))
        await page.close()
        await browser.close()

    all_ok = True
    for pn, r in results.items():
        ok = not r["errors390"] and not r["hscroll390"] and not r["hscroll1280"]
        all_ok = all_ok and ok
        print(f"{pn}: {'PASS' if ok else 'FAIL'} | err390={r['errors390']} h390={r['hscroll390']} h1280={r['hscroll1280']}")
    with open(os.path.join(EVID, "verify_result.json"), "w", encoding="utf-8") as fh:
        json.dump(results, fh, ensure_ascii=False, indent=1, default=str)
    print("ALL PASS" if all_ok else "SOME FAIL")
    sys.exit(0 if all_ok else 1)

asyncio.run(main())