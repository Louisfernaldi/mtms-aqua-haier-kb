# -*- coding: utf-8 -*-
"""verify_proses.py — Cek halaman Proses (proses.html) render timeline + kartu tugas.

Playwright (async) + Chrome, buka file:///.../site/proses.html di viewport 1280x800,
cek (semua WAJIB lolos):
  - document.querySelectorAll('.tl-step').length >= 8
  - 0 paragraf dengan teks > 320 karakter di dalam #konten-proses
  - 0 console error / pageerror

Print angka + isi tiap langkah timeline (nomor, judul, badge status, PIC, detail).
Exit 0 kalau lolos semua, selain itu 1 + pesan jelas.
"""
import asyncio
import sys
from playwright.async_api import async_playwright

SITE_DIR = r"D:/AI/projects/mtms-aqua-haier-kb/site"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
PAGE = "proses.html"

MIN_STEPS = 8
MAX_PARA_LEN = 320


async def main():
    errs = []
    steps = 0
    long_paras = []
    step_lines = []
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(executable_path=CHROME)
        page = await browser.new_page(viewport={"width": 1280, "height": 800})
        page.on("console", lambda m: errs.append("console-%s: %s" % (m.type, m.text)) if m.type == "error" else None)
        page.on("pageerror", lambda e: errs.append("pageerror: %s" % e))
        await page.goto("file:///" + SITE_DIR + "/" + PAGE, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(1200)
        steps = await page.evaluate("document.querySelectorAll('.tl-step').length")
        step_lines = await page.evaluate(
            "Array.from(document.querySelectorAll('.tl-step')).map(function(s){"
            "var num=s.querySelector('.tl-num');var t=s.querySelector('.tl-title');var b=s.querySelector('.tl-badge');"
            "var p=s.querySelector('.tl-pic');var d=s.querySelector('.tl-detail');"
            "return (num?num.textContent.trim():'')+' | '+(t?t.textContent.trim():'')+' | '+(b?b.textContent.trim():'')"
            "+' | '+(p?p.textContent.trim():'')+' | '+(d?d.textContent.trim():'');})"
        )
        long_paras = await page.evaluate(
            "Array.from(document.querySelectorAll('#konten-proses p')).map(function(p){"
            "return {teks:p.textContent.trim(), len:p.textContent.trim().length};"
            "}).filter(function(o){return o.len > %d;})" % MAX_PARA_LEN
        )
        await browser.close()

    print("halaman: %s" % PAGE)
    print("langkah timeline (.tl-step): %d (min %d)" % (steps, MIN_STEPS))
    for ln in step_lines:
        print("  [step] " + ln)
    print("paragraf >%d karakter di #konten-proses: %d" % (MAX_PARA_LEN, len(long_paras)))
    for o in long_paras:
        print("  [panjang] len=%d teks=%s" % (o["len"], o["teks"][:80]))
    print("console error: %d" % len(errs))
    for e in errs[:10]:
        print("  " + e)

    ok = True
    if steps < MIN_STEPS:
        print("GAGAL: langkah timeline kurang dari %d (ditemukan %d)" % (MIN_STEPS, steps))
        ok = False
    if long_paras:
        print("GAGAL: ada %d paragraf >%d karakter di #konten-proses" % (len(long_paras), MAX_PARA_LEN))
        ok = False
    if errs:
        print("GAGAL: ada %d console error / pageerror" % len(errs))
        ok = False
    if ok:
        print("verify_proses: LULUS")
    sys.exit(0 if ok else 1)


asyncio.run(main())
