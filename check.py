#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gate W2 produk.html P0 - 3 temuan §2
JANGAN diedit Codex; tugas Codex bikin kode sampai check.py lolos.
"""
import re, sys, pathlib

root = pathlib.Path(__file__).parent
css_path = root / "site" / "css" / "style.css"
js_path  = root / "site" / "js" / "produk.js"
html_path= root / "site" / "produk.html"

def fail(msg):
    print(f"FAIL: {msg}")
    return False

def ok(msg):
    print(f"OK: {msg}")
    return True

all_ok = True

# --- baca file ---
try:
    css = css_path.read_text(encoding="utf-8")
except Exception as e:
    print(f"FAIL: tidak bisa baca {css_path}: {e}")
    sys.exit(1)
try:
    js = js_path.read_text(encoding="utf-8")
except Exception as e:
    print(f"FAIL: tidak bisa baca {js_path}: {e}")
    sys.exit(1)
try:
    html = html_path.read_text(encoding="utf-8")
except Exception as e:
    print(f"FAIL: tidak bisa baca {html_path}: {e}")
    sys.exit(1)

# Helper extract block
def extract_rule(css_text, selector):
    # naive: find selector then { ... }
    m = re.search(re.escape(selector) + r"\s*\{([^}]*)\}", css_text, re.DOTALL)
    return m.group(1) if m else None

# 1) Keterbacaan teks
print("=== 1. Keterbacaan teks (pk-meta 0.88, pk-cat 0.8, badge 0.75) ===")
# .pk-meta
pk_meta_block = extract_rule(css, ".pk-meta")
if not pk_meta_block:
    all_ok = fail(".pk-meta rule tidak ditemukan") and all_ok
else:
    if "0.88rem" in pk_meta_block:
        all_ok = ok(".pk-meta font-size 0.88rem ditemukan") and all_ok
    else:
        all_ok = fail(f".pk-meta harus 0.88rem, blok: {pk_meta_block.strip()[:200]}") and all_ok
    # cek line-height 1.5
    if re.search(r"line-height\s*:\s*1\.5", pk_meta_block):
        all_ok = ok(".pk-meta line-height 1.5") and all_ok
    else:
        # alternatively cek shorthand font 0.88rem/1.5
        if "0.88rem/1.5" in pk_meta_block or "0.88rem / 1.5" in pk_meta_block:
            all_ok = ok(".pk-meta 0.88/1.5 shorthand") and all_ok
        else:
            all_ok = fail(f".pk-meta line-height 1.5 tidak ada, blok: {pk_meta_block.strip()[:200]}") and all_ok
    # cek warna contrast: harus #3d5a6b atau var(--text) (bukan var(--text-muted) terang)
    if "#3d5a6b" in pk_meta_block or "var(--text)" in pk_meta_block:
        # but ensure not only muted? if contains #3d5a6b or var(--text) it's ok even if also muted exists elsewhere
        # lebih ketat: blok harus mengandung #3d5a6b atau color: var(--text)
        all_ok = ok(f".pk-meta warna contrast ({'#3d5a6b' if '#3d5a6b' in pk_meta_block else 'var(--text)'})") and all_ok
    else:
        # jika masih var(--text-muted) tapi opacity 0.9 hilang maybe ok? spec says bukan muted terang
        if "var(--text-muted)" in pk_meta_block:
            all_ok = fail(".pk-meta masih var(--text-muted) — harus #3d5a6b atau var(--text) untuk contrast") and all_ok
        else:
            all_ok = fail(f".pk-meta warna harus #3d5a6b atau var(--text), blok: {pk_meta_block.strip()[:200]}") and all_ok

# .pk-cat
pk_cat_block = extract_rule(css, ".pk-cat")
if not pk_cat_block:
    all_ok = fail(".pk-cat rule tidak ditemukan") and all_ok
else:
    if "0.8rem" in pk_cat_block:
        # ensure not 0.75rem left — check that 0.8 is present and prioritized
        all_ok = ok(".pk-cat font-size 0.8rem") and all_ok
    else:
        all_ok = fail(f".pk-cat harus 0.8rem, blok: {pk_cat_block.strip()[:200]}") and all_ok
    # pastikan bukan 0.75 masih ada tanpa 0.8
    if "0.75rem" in pk_cat_block and "0.8rem" not in pk_cat_block:
        all_ok = fail(".pk-cat masih 0.75rem") and all_ok

# .badge
badge_block = extract_rule(css, ".badge")
if not badge_block:
    all_ok = fail(".badge rule tidak ditemukan") and all_ok
else:
    if "0.75rem" in badge_block:
        all_ok = ok(".badge font-size 0.75rem") and all_ok
    else:
        all_ok = fail(f".badge harus 0.75rem, blok: {badge_block.strip()[:200]}") and all_ok
    # font-weight 600
    if re.search(r"font-weight\s*:\s*600", badge_block):
        all_ok = ok(".badge font-weight 600") and all_ok
    else:
        all_ok = fail(f".badge font-weight harus 600, blok: {badge_block.strip()[:200]}") and all_ok
    # jangan masih 700 tanpa 600? badge 0.7 juga harus hilang
    if "700" in badge_block and "600" not in badge_block:
        all_ok = fail(".badge masih 700, harus 600") and all_ok

# 2) Proporsi gambar placeholder
print("\n=== 2. Placeholder pk-noimg SVG dashed ===")
# CSS .pk-thumb.pk-noimg
thumb_noimg_block = extract_rule(css, ".pk-thumb.pk-noimg")
if not thumb_noimg_block:
    all_ok = fail(".pk-thumb.pk-noimg rule tidak ditemukan") and all_ok
else:
    checks = []
    # harus contain SVG inline via CSS? sebenarnya thumb_noimg harus flex column gap + dashed + bg #f4f8fb + aspect
    if "dashed" in thumb_noimg_block:
        all_ok = ok(".pk-thumb.pk-noimg border dashed") and all_ok
    else:
        all_ok = fail(f".pk-thumb.pk-noimg harus border dashed, blok: {thumb_noimg_block.strip()[:300]}") and all_ok
    if "#f4f8fb" in thumb_noimg_block or "var(--border)" in thumb_noimg_block:
        # need both: border 1px dashed var(--border) bg #f4f8fb
        if "#f4f8fb" in thumb_noimg_block:
            all_ok = ok(".pk-thumb.pk-noimg bg #f4f8fb") and all_ok
        else:
            all_ok = fail(f".pk-thumb.pk-noimg bg harus #f4f8fb, blok: {thumb_noimg_block.strip()[:300]}") and all_ok
        if "var(--border)" in thumb_noimg_block:
            all_ok = ok(".pk-thumb.pk-noimg border var(--border)") and all_ok
        else:
            all_ok = fail(f".pk-thumb.pk-noimg border harus var(--border), blok: {thumb_noimg_block.strip()[:300]}") and all_ok
    else:
        all_ok = fail(f".pk-thumb.pk-noimg harus bg #f4f8fb dan border var(--border), blok: {thumb_noimg_block.strip()[:300]}") and all_ok
    # aspect 1/1
    if "aspect-ratio" in thumb_noimg_block and "1" in thumb_noimg_block:
        # cek 1/1
        if re.search(r"aspect-ratio\s*:\s*1\s*/\s*1", thumb_noimg_block):
            all_ok = ok(".pk-thumb.pk-noimg aspect-ratio 1/1") and all_ok
        else:
            all_ok = fail(f".pk-thumb.pk-noimg aspect-ratio harus 1/1, blok: {thumb_noimg_block.strip()[:300]}") and all_ok
    else:
        all_ok = fail(f".pk-thumb.pk-noimg aspect-ratio 1/1 tidak ada, blok: {thumb_noimg_block.strip()[:300]}") and all_ok
    # flex column gap
    if "flex" in thumb_noimg_block and "column" in thumb_noimg_block:
        all_ok = ok(".pk-thumb.pk-noimg flex column") and all_ok
    else:
        all_ok = fail(f".pk-thumb.pk-noimg harus flex column, blok: {thumb_noimg_block.strip()[:300]}") and all_ok
    if "gap" in thumb_noimg_block:
        all_ok = ok(".pk-thumb.pk-noimg gap") and all_ok
    else:
        all_ok = fail(f".pk-thumb.pk-noimg harus gap, blok: {thumb_noimg_block.strip()[:300]}") and all_ok
    # bukan emoji besar 3rem lagi, should contain svg related? CSS shouldn't have font-size 3rem alone
    if "font-size: 3rem" in thumb_noimg_block or "font-size:3rem" in thumb_noimg_block:
        all_ok = fail(".pk-thumb.pk-noimg masih font-size 3rem emoji — harus SVG") and all_ok
    else:
        all_ok = ok(".pk-thumb.pk-noimg tidak pakai emoji 3rem") and all_ok
    # background previously var(--bg-soft) #eaf3fa should not dominate
    if "#eaf3fa" in css and thumb_noimg_block and "#eaf3fa" in thumb_noimg_block:
        all_ok = fail(".pk-thumb.pk-noimg masih #eaf3fa — harus #f4f8fb") and all_ok

# JS thumb function
print("\n--- JS thumb(p) ---")
if "pk-noimg" in js and "<svg" in js:
    all_ok = ok("produk.js pk-noimg mengandung <svg") and all_ok
else:
    all_ok = fail("produk.js thumb harus contain '<svg' dan 'pk-noimg'") and all_ok
if "Belum ada foto" in js:
    all_ok = ok('produk.js thumb mengandung "Belum ada foto"') and all_ok
else:
    all_ok = fail('produk.js thumb harus label "Belum ada foto · AQR-..."') and all_ok
# cek SVG siluet kulkas: rect + stroke-dasharray + lines
if 'stroke-dasharray="4 2"' in js or "stroke-dasharray" in js:
    all_ok = ok("produk.js SVG stroke-dasharray") and all_ok
else:
    all_ok = fail("produk.js SVG harus stroke-dasharray='4 2'") and all_ok
if 'viewBox="0 0 48 48"' in js:
    all_ok = ok("produk.js SVG viewBox 48") and all_ok
else:
    all_ok = fail("produk.js SVG viewBox 0 0 48 48 tidak ada") and all_ok
# cek tidak masih emoji
if "pk-noimg\" aria-hidden=\"true\">❄️" in js or "pk-noimg\">❄️" in js or "❄️" in js and "pk-noimg" in js and "<svg" not in js:
    all_ok = fail("produk.js masih emoji ❄️ sebagai placeholder") and all_ok
# more precise: if file contains emoji thumb return, fail
if re.search(r"pk-noimg.*❄", js):
    # but if also contains svg, check which thumb return is used
    if "<svg" in js:
        # ensure emoji not in pk-noimg return string
        # find thumb function block
        thumb_match = re.search(r"function thumb\(p\)\s*\{[^}]+\}", js, re.DOTALL)
        if thumb_match and "❄" in thumb_match.group(0):
            all_ok = fail("function thumb(p) masih mengandung emoji ❄️ — harus SVG") and all_ok
        else:
            all_ok = ok("thumb emoji sudah diganti SVG") and all_ok
    else:
        all_ok = fail("thumb masih emoji ❄️") and all_ok
else:
    all_ok = ok("thumb tidak mengandung emoji") and all_ok

# cek span model suffix 0.8rem logic
if '0.8rem' in js or "0.8rem" in css:
    # CSS untuk span inside pk-noimg should be 0.8rem
    if re.search(r"\.pk-thumb\.pk-noimg\s*span|\.pk-noimg\s*span|pk-noimg.*0\.8rem", css, re.DOTALL):
        all_ok = ok("CSS span placeholder 0.8rem") and all_ok
    else:
        # cari di css apakah ada font-size 0.8rem untuk span dalam pk-noimg
        # alternative check: cari css block mengandung pk-noimg span
        if ".pk-thumb.pk-noimg span" in css or ".pk-noimg span" in css:
            # check that block has 0.8rem
            span_block = re.search(r"\.pk-thumb\.pk-noimg\s+span\s*\{([^}]*)\}", css, re.DOTALL)
            if span_block and "0.8rem" in span_block.group(1):
                all_ok = ok("pk-noimg span 0.8rem") and all_ok
            else:
                all_ok = fail("CSS .pk-thumb.pk-noimg span harus 0.8rem") and all_ok
        else:
            # JS inline style maybe
            if '0.8rem' in js and 'Belum ada foto' in js:
                all_ok = ok("label placeholder 0.8rem via inline/JS or CSS") and all_ok
            else:
                print("WARN: CSS span 0.8rem tidak ditemukan explicit — cek manual")
else:
    print("WARN: 0.8rem untuk label placeholder tidak terdeteksi")

# 3) Hierarki paging
print("\n=== 3. Hierarki paging (chips sticky, pagination 12/page, counter) ===")

# CSS chips sticky
pk_chips_block = extract_rule(css, ".pk-chips")
if not pk_chips_block:
    all_ok = fail(".pk-chips rule tidak ditemukan") and all_ok
else:
    if "position" in pk_chips_block and "sticky" in pk_chips_block:
        all_ok = ok(".pk-chips position sticky") and all_ok
    else:
        all_ok = fail(f".pk-chips harus position: sticky, blok: {pk_chips_block.strip()[:300]}") and all_ok
    if re.search(r"top\s*:\s*60px", pk_chips_block):
        all_ok = ok(".pk-chips top 60px") and all_ok
    else:
        all_ok = fail(f".pk-chips top harus 60px, blok: {pk_chips_block.strip()[:300]}") and all_ok
    if "z-index" in pk_chips_block and re.search(r"z-index\s*:\s*5", pk_chips_block):
        all_ok = ok(".pk-chips z-index 5") and all_ok
    else:
        all_ok = fail(f".pk-chips z-index harus 5, blok: {pk_chips_block.strip()[:300]}") and all_ok
    if "var(--bg)" in pk_chips_block:
        all_ok = ok(".pk-chips bg var(--bg)") and all_ok
    else:
        all_ok = fail(f".pk-chips bg harus var(--bg), blok: {pk_chips_block.strip()[:300]}") and all_ok
    if re.search(r"padding\s*:\s*8px\s+0", pk_chips_block):
        all_ok = ok(".pk-chips padding 8px 0") and all_ok
    else:
        all_ok = fail(f".pk-chips padding harus 8px 0, blok: {pk_chips_block.strip()[:300]}") and all_ok

# CSS grid
pk_grid_block = extract_rule(css, ".pk-grid")
if not pk_grid_block:
    all_ok = fail(".pk-grid rule tidak ditemukan") and all_ok
else:
    if "minmax(260px" in pk_grid_block:
        all_ok = ok(".pk-grid minmax 260px") and all_ok
    else:
        all_ok = fail(f".pk-grid harus minmax(260px), blok: {pk_grid_block.strip()[:200]}") and all_ok

# JS pagination
print("\n--- JS pagination ---")
# state page perPage
if re.search(r"state\s*=\s*\{[^}]*page\s*:\s*1[^}]*perPage\s*:\s*12", js, re.DOTALL) or (re.search(r"page\s*:\s*1", js) and re.search(r"perPage\s*:\s*12", js)):
    all_ok = ok("state.page 1 dan perPage 12 ditemukan") and all_ok
else:
    all_ok = fail("state harus {group, q, page:1, perPage:12} — page/perPage 12 tidak ditemukan") and all_ok

# slice
if re.search(r"slice\s*\(\s*\(?\s*page\s*-\s*1\s*\)\s*\*\s*perPage", js) or re.search(r"\.slice\(.*perPage", js):
    all_ok = ok("render slice (page-1)*perPage .. page*perPage") and all_ok
else:
    all_ok = fail("render harus slice list dengan (page-1)*perPage") and all_ok

# pagination container
if "pk-pagination" in js and "pk-pagination" in css:
    all_ok = ok("pk-pagination ada di JS dan CSS") and all_ok
elif "pk-pagination" in js:
    all_ok = fail("pk-pagination ada di JS tapi tidak di CSS") and all_ok
else:
    all_ok = fail("pk-pagination tidak ditemukan di JS") and all_ok

# prev/next buttons
if "Prev" in js and "Next" in js:
    all_ok = ok("Prev/Next buttons ada") and all_ok
else:
    all_ok = fail("Pagination harus ada Prev/Next") and all_ok

# ellipsis jika >5 pages
if "ellipsis" in js.lower() or "..." in js or "…" in js:
    all_ok = ok("Ellipsis logic ada") and all_ok
else:
    print("WARN: ellipsis logic tidak terdeteksi explicit — cek manual (harus ada jika >5 pages)")

# chips onclick reset page 1
if re.search(r"state\.page\s*=\s*1", js):
    all_ok = ok("chips onclick reset page 1") and all_ok
else:
    all_ok = fail("chips onclick harus reset state.page=1") and all_ok

# counter tegas "Menampilkan 12 dari 74" di info
if "Menampilkan" in js:
    # cek format menampilkan X dari Y atau menampilkan slice count
    if re.search(r"Menampilkan.*dari", js):
        all_ok = ok('counter "Menampilkan ... dari ..." ada') and all_ok
    else:
        all_ok = fail('counter harus "Menampilkan 12 dari 74" format') and all_ok
    # cek bukan hanya list.length tapi paginated count
    if re.search(r"Menampilkan.*slice|Menampilkan.*perPage|Menampilkan.*\(page", js) or re.search(r"info\.textContent.*Menampilkan", js):
        # additional check slice count
        if re.search(r"slice|perPage", js):
            all_ok = ok("counter terkait pagination slice") and all_ok
        else:
            print("WARN: counter mungkin masih menampilkan total tanpa slice")
    else:
        print("WARN: counter belum tentu akurat pagination")
else:
    all_ok = fail('counter "Menampilkan" tidak ditemukan') and all_ok

# cek active class untuk pagination buttons .on
if ".on" in js or '"on"' in js or "'on'" in js or "active" in js:
    all_ok = ok("pagination active/on class ada") and all_ok
else:
    all_ok = fail("pagination buttons harus .on active class") and all_ok

# cek perPage options 12/24?
if "12" in js and "24" in js:
    all_ok = ok("12/24 per page refs ada") and all_ok
else:
    print("WARN: 24 per page belum tentu ada — spec minta 12/24 per page")

# HTML pagination container minimal
if "pk-pagination" in html or "pk-pagination" in js:
    all_ok = ok("HTML/JS pagination container ada") and all_ok
else:
    all_ok = fail("produk.html atau JS harus ada div pk-pagination") and all_ok

print("\n=== RINGKASAN ===")
if all_ok:
    print("SEMUA CEK LULUS ✅ — W2 siap")
    sys.exit(0)
else:
    print("MASIH ADA FAIL ❌ — perbaiki sebelum selesai")
    sys.exit(1)
