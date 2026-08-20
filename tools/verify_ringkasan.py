# -*- coding: utf-8 -*-
"""verify_ringkasan.py — Cek section "Ringkasan Pengetahuan" visual di produk.html.

Playwright (async) + Chrome, buka file:///.../site/produk.html di viewport 1280x800,
cek (semua WAJIB lolos):
  - document.querySelectorAll('#ringkasan-visual table tbody tr').length >= 5
  - document.querySelectorAll('.stat-card').length >= 4
  - 0 console error / pageerror

Print semua angka (jumlah baris tabel, jumlah stat-card, isi tiap baris & kartu).
Exit 0 kalau lolos semua, selain itu 1 + pesan jelas.
"""
import asyncio
import sys
from playwright.async_api import async_playwright

SITE_DIR = r"D:/AI/projects/mtms-aqua-haier-kb/site"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
PAGE = "produk.html"

MIN_ROWS = 5
MIN_STAT = 4


async def main():
    errs = []
    rows = 0
    stats = 0
    row_texts = []
    stat_texts = []
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(executable_path=CHROME)
        page = await browser.new_page(viewport={"width": 1280, "height": 800})
        page.on("console", lambda m: errs.append("console-%s: %s" % (m.type, m.text)) if m.type == "error" else None)
        page.on("pageerror", lambda e: errs.append("pageerror: %s" % e))
        await page.goto("file:///" + SITE_DIR + "/" + PAGE, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(1200)
        rows = await page.evaluate("document.querySelectorAll('#ringkasan-visual table tbody tr').length")
        stats = await page.evaluate("document.querySelectorAll('.stat-card').length")
        row_texts = await page.evaluate(
            "Array.from(document.querySelectorAll('#ringkasan-visual table tbody tr')).map(function(tr){"
            "return Array.from(tr.querySelectorAll('td')).map(function(td){return td.textContent.trim();}).join(' | ');})"
        )
        stat_texts = await page.evaluate(
            "Array.from(document.querySelectorAll('.stat-card')).map(function(c){"
            "return (c.querySelector('b') ? c.querySelector('b').textContent.trim() : '') + ' = ' + "
            "(c.querySelector('span') ? c.querySelector('span').textContent.trim() : '');})"
        )
        await browser.close()

    print("halaman: %s" % PAGE)
    print("baris tabel #ringkasan-visual table tbody tr: %d (min %d)" % (rows, MIN_ROWS))
    for t in row_texts:
        print("  [tabel] " + t)
    print("stat-card: %d (min %d)" % (stats, MIN_STAT))
    for t in stat_texts:
        print("  [stat] " + t)
    print("console error: %d" % len(errs))
    for e in errs[:10]:
        print("  " + e)

    ok = True
    if rows < MIN_ROWS:
        print("GAGAL: baris tabel segmen kurang dari %d (ditemukan %d)" % (MIN_ROWS, rows))
        ok = False
    if stats < MIN_STAT:
        print("GAGAL: stat-card kurang dari %d (ditemukan %d)" % (MIN_STAT, stats))
        ok = False
    if errs:
        print("GAGAL: ada %d console error / pageerror" % len(errs))
        ok = False
    if ok:
        print("verify_ringkasan: LULUS")
    sys.exit(0 if ok else 1)


asyncio.run(main())