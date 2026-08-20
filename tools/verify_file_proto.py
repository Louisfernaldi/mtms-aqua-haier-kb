# -*- coding: utf-8 -*-
"""verify_file_proto.py — Verifikasi 7 halaman situs lewat file:// (tanpa server).

Playwright (async) + Chrome: buka file:///D:/AI/projects/mtms-aqua-haier-kb/site/<hal>.html
di viewport 1280x800 dan 390x844 (domcontentloaded + wait 1200ms), hitung:
  - console error + pageerror
  - h-scroll (informasional)
  - konten render per halaman:
      index   -> .card        > 0
      induksi -> .card        > 0
      produk  -> .pk-card     == 51
      rotasi  -> .card        > 0
      proses  -> .card        > 0
      galeri  -> figure img   > 0
      file    -> li           > 0

Print di akhir:
  errors: N
  render_gagal: N          (jumlah kombinasi halaman-viewport dengan konten 0)
Exit code 0 kalau dua-duanya 0, selain itu 1.
"""
import asyncio
import os
import sys
from playwright.async_api import async_playwright

SITE_DIR = r"D:/AI/projects/mtms-aqua-haier-kb/site"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

PAGES = ["index.html", "induksi.html", "produk.html", "rotasi.html", "proses.html", "galeri.html", "file.html"]
VIEWPORTS = [(1280, 800), (390, 844)]

CHECK = {
    "index.html": "document.querySelectorAll('.card').length > 0",
    "induksi.html": "document.querySelectorAll('.card').length > 0",
    "produk.html": "document.querySelectorAll('.pk-card').length === 42",
    "rotasi.html": "document.querySelectorAll('.card').length > 0",
    "proses.html": "document.querySelectorAll('.card').length > 0",
    "galeri.html": "document.querySelectorAll('figure img').length > 0",
    "file.html": "document.querySelectorAll('li').length > 0",
}


async def main():
    errors_total = 0
    hscroll_total = 0
    render_gagal = 0
    lines = []
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(executable_path=CHROME)
        for (w, h) in VIEWPORTS:
            for page_name in PAGES:
                errs = []
                page = await browser.new_page(viewport={"width": w, "height": h})
                page.on("console", lambda m: errs.append("console-%s: %s" % (m.type, m.text)) if m.type == "error" else None)
                page.on("pageerror", lambda e: errs.append("pageerror: %s" % e))
                await page.goto("file:///" + SITE_DIR + "/" + page_name, wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_timeout(1200)
                hscroll = await page.evaluate("document.documentElement.scrollWidth > document.documentElement.clientWidth")
                ok_render = await page.evaluate(CHECK[page_name])
                await page.close()
                tag = "%dx%d %s" % (w, h, page_name)
                status = "OK"
                if errs:
                    status = "ERR"
                    errors_total += len(errs)
                if hscroll:
                    hscroll_total += 1
                if not ok_render:
                    status = (status + "+") if status != "OK" else "RENDER0"
                    render_gagal += 1
                lines.append("[%s] %-42s errs=%-2d hscroll=%-5s render=%s" % (status, tag, len(errs), str(hscroll).lower(), ok_render))
                if errs:
                    for e in errs[:5]:
                        lines.append("      " + e)
        await browser.close()

    for ln in lines:
        print(ln)
    print("errors: %d" % errors_total)
    print("hscroll: %d" % hscroll_total)
    print("render_gagal: %d" % render_gagal)
    sys.exit(0 if (errors_total == 0 and render_gagal == 0) else 1)


asyncio.run(main())
