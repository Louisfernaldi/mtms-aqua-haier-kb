#!/usr/bin/env python3
# check_w1.py — Gerbang W1 kompetitor.html P0 (6 temuan)
# JANGAN DIEDIT CODEX — file ini gerbang verifikasi, bukan target edit.
import re, pathlib, sys

root = pathlib.Path(__file__).parent
html_path = root / "site" / "kompetitor.html"
css_path = root / "site" / "css" / "style.css"

def read(p): return p.read_text(encoding="utf-8")

html = read(html_path)
css = read(css_path)

fails = []

def fail(msg): fails.append(msg)

# --- helper: extract CSS block for selector
def css_block(pattern, text):
    # find all occurrences
    m = re.search(pattern, text, re.DOTALL)
    return m.group(0) if m else ""

# 1. .comp-fitur-list li 0.75rem line-height 1.5 color var(--text) clamp 3 baris
# Check both files: inline <style> in html and style.css
for fname, content in [("site/css/style.css", css), ("site/kompetitor.html", html)]:
    # cari blok .comp-fitur-list li
    blocks = re.findall(r"\.comp-fitur-list\s+li\s*\{[^}]+\}", content, re.DOTALL)
    if not blocks:
        fail(f"[1] {fname}: blok .comp-fitur-list li tidak ditemukan")
        continue
    block = "\n".join(blocks)
    if "0.75rem" not in block:
        fail(f"[1] {fname}: .comp-fitur-list li harus font-size 0.75rem (found: {block[:120]})")
    if "1.5" not in block:
        fail(f"[1] {fname}: .comp-fitur-list li harus line-height 1.5")
    if "var(--text)" not in block and "#12303f" not in block:
        fail(f"[1] {fname}: .comp-fitur-list li harus color var(--text) / #12303f")
    if "-webkit-line-clamp" not in block or "3" not in block:
        fail(f"[1] {fname}: .comp-fitur-list li harus -webkit-line-clamp:3")
    if "-webkit-box-orient" not in block or "vertical" not in block:
        fail(f"[1] {fname}: .comp-fitur-list li harus -webkit-box-orient:vertical")
    if "display:" not in block or "-webkit-box" not in block:
        fail(f"[1] {fname}: .comp-fitur-list li harus display:-webkit-box")
    if "overflow:hidden" not in block.replace(" ",""):
        fail(f"[1] {fname}: .comp-fitur-list li harus overflow:hidden")
# also check tooltip title tetap: fiturHtml should have title attribute
if "title" not in html.lower() or "comp-fitur-list" not in html:
    # check JS fiturHtml generates title
    if 'title=' not in html:
        fail("[1] JS fiturHtml harus tetap punya title tooltip (title attribute di <li>)")

# 2. .comp-meta pecah 2 baris, harga 0.78rem bold var(--accent-dark), hapus nowrap, line-height 1.4
for fname, content in [("site/css/style.css", css), ("site/kompetitor.html", html)]:
    blocks = re.findall(r"\.comp-meta\s*\{[^}]+\}", content, re.DOTALL)
    if not blocks:
        # coba cari .comp-meta tanpa blok? mungkin sudah dipecah jadi inner
        if fname=="site/css/style.css":
            fail(f"[2] {fname}: blok .comp-meta tidak ditemukan")
        continue
    block = "\n".join(blocks)
    if "white-space:nowrap" in block.replace(" ","") or "white-space: nowrap" in block:
        fail(f"[2] {fname}: .comp-meta harus HAPUS white-space:nowrap")
    if "1.4" not in block:
        fail(f"[2] {fname}: .comp-meta harus line-height 1.4")
    # harus ada harga 0.78rem di css (bisa di .comp-meta atau .comp-price/.comp-meta-price)
    if "0.78rem" not in content:
        fail(f"[2] {fname}: harus ada harga 0.78rem (bold var(--accent-dark)) di CSS")
    if "var(--accent-dark)" not in content:
        fail(f"[2] {fname}: harus ada var(--accent-dark) untuk harga")
# check html JS pecah 2 baris kapasitas di atas harga: cari fitur renderRow memecah comp-meta jadi 2 elemen
if "comp-meta" in html:
    # cari apakah ada &middot; masih dipakai (harusnya tidak, pecah 2 baris)
    # toleransi: jika masih ada &middot; dianggap gagal pecah
    # tapi cek juga apakah ada 2 span/div untuk cap dan price
    if "&middot;" in html and "comp-price" not in html and "comp-cap" not in html:
        fail("[2] site/kompetitor.html: comp-meta masih pakai '&middot;' — harus pecah 2 baris kapasitas di atas, harga di bawah")
    if "0.78rem" not in html and "0.78rem" not in css:
        fail("[2] harga 0.78rem tidak ditemukan di html/css")
else:
    fail("[2] site/kompetitor.html: .comp-meta tidak ditemukan")

# 3. Tombol .comp-row-actions button 0.75rem 6px 12px min-height 32px min-width 40px gap 6px + ikon
for fname, content in [("site/css/style.css", css), ("site/kompetitor.html", html)]:
    blocks = re.findall(r"\.comp-row-actions\s+button\s*\{[^}]+\}", content, re.DOTALL)
    if not blocks:
        if fname=="site/css/style.css":
            fail(f"[3] {fname}: blok .comp-row-actions button tidak ditemukan")
        continue
    block = "\n".join(blocks)
    if "0.75rem" not in block:
        fail(f"[3] {fname}: button harus font-size 0.75rem")
    if "6px" not in block or "12px" not in block:
        fail(f"[3] {fname}: button harus padding 6px 12px")
    if "32px" not in block:
        fail(f"[3] {fname}: button harus min-height 32px")
    if "40px" not in block:
        fail(f"[3] {fname}: button harus min-width 40px")
# gap 6px bisa di .comp-row-actions atau button
gap_found = ("gap:6px" in css.replace(" ","") or "gap: 6px" in css) or ("gap:6px" in html.replace(" ","") or "gap: 6px" in html)
if not gap_found:
    fail("[3] gap 6px tidak ditemukan di .comp-row-actions (harus gap 6px)")

# ikon ✎ / 🗑 di JS renderRow
if "✎" not in html:
    fail("[3] site/kompetitor.html: ikon ✎ tidak ditemukan di JS renderRow (button Edit harus ada ✎)")
if "🗑" not in html:
    fail("[3] site/kompetitor.html: ikon 🗑 tidak ditemukan di JS renderRow (button Hapus harus ada 🗑)")
# cek textContent aman: harus pakai textContent atau esc() bukan hardcode HTML innerHTML mentah untuk user data
# minimal cek ada esc() atau textContent di sekitar renderRow
if "textContent" not in html and "esc(" not in html:
    fail("[3] JS harus pakai textContent aman (tidak hardcode HTML)")
# cek bukan hardcode HTML mentah untuk button label (pastikan ada esc atau createElement)
# kita longgar: kalau ada ✎ dan 🗑 sudah ok

# 4. Sticky header th position:sticky top 58px z-index 5 bg var(--accent-dark) color #fff, .comp-cat-header sticky top 58px
# cek css th sticky
th_blocks = re.findall(r"\.comp-full-table\s+th\s*\{[^}]+\}", css, re.DOTALL)
html_th_blocks = re.findall(r"\.comp-full-table\s+th\s*\{[^}]+\}", html, re.DOTALL)
combined_th = "\n".join(th_blocks + html_th_blocks)
if "position:sticky" not in combined_th.replace(" ","") and "position: sticky" not in combined_th:
    fail("[4] .comp-full-table th harus position:sticky")
if "58px" not in combined_th:
    fail("[4] th harus top 58px (header 60px)")
if "z-index" not in combined_th or "5" not in combined_th:
    fail("[4] th harus z-index 5")
if "var(--accent-dark)" not in combined_th:
    fail("[4] th harus background var(--accent-dark)")
if "#fff" not in combined_th and "#ffffff" not in combined_th.lower() and "color:#fff" not in combined_th.replace(" ",""):
    fail("[4] th harus color #fff")
# .comp-cat-header sticky
cat_blocks = re.findall(r"\.comp-cat-header\s*\{[^}]+\}", css, re.DOTALL) + re.findall(r"\.comp-cat-header\s*\{[^}]+\}", html, re.DOTALL)
cat_combined = "\n".join(cat_blocks)
if "position:sticky" not in cat_combined.replace(" ","") and "position: sticky" not in cat_combined:
    fail("[4] .comp-cat-header harus position:sticky")
if "58px" not in cat_combined:
    fail("[4] .comp-cat-header harus top 58px")

# 5. min-width 1080px, AQUA sticky left:0 box-shadow z-index 4, fade kanan ::after gradient
if "1080px" not in css and "1080px" not in html:
    fail("[5] desktop min-width harus 1080px (sekarang masih 900px)")
if "900px" in css and "1080px" not in css:
    fail("[5] css masih mengandung min-width 900px, harus ganti 1080px")
# cek AQUA sticky left:0
aqua_sticky_found = False
# cari selector th:first-child atau td:first-child atau .comp-cell.comp-aqua atau .comp-aqua dengan sticky
if "left:0" in css.replace(" ","") or "left: 0" in css:
    if "sticky" in css and ("comp-aqua" in css or "first-child" in css):
        aqua_sticky_found = True
if not aqua_sticky_found:
    # cek juga html inline style
    if "left:0" in html.replace(" ","") and "sticky" in html:
        aqua_sticky_found = True
if not aqua_sticky_found:
    fail("[5] kolom AQUA harus sticky left:0 (th:first-child / td.comp-aqua position:sticky)")
if "box-shadow" not in css or "2px 0 8px" not in css:
    if "box-shadow" not in html:
        fail("[5] AQUA sticky harus box-shadow 2px 0 8px rgba(0,0,0,.08)")
if "z-index" in css:
    # need z-index 4 for AQUA column
    if "z-index:4" not in css.replace(" ","") and "z-index: 4" not in css:
        # cek html
        if "z-index:4" not in html.replace(" ","") and "z-index: 4" not in html:
            fail("[5] AQUA sticky harus z-index 4")
# fade kanan ::after gradient di .comp-table-wrap
if ".comp-table-wrap::after" not in css and ".comp-table-wrap:after" not in css and ".comp-table-wrap::after" not in html:
    fail("[5] .comp-table-wrap harus punya ::after gradient fade kanan")
else:
    fade_block = ""
    if ".comp-table-wrap::after" in css:
        # ambil sekitar
        idx = css.find(".comp-table-wrap::after")
        fade_block = css[idx:idx+600]
        if "gradient" not in fade_block:
            fail("[5] ::after harus gradient (linear-gradient)")

# 6. Empty ghost subtle border transparent bg var(--bg-soft) opacity 0.7 hover accent solid text "＋ Model" lebih kecil
# cek .comp-add-cell
add_blocks = re.findall(r"\.comp-add-cell\s*\{[^}]+\}", css, re.DOTALL) + re.findall(r"\.comp-add-cell\s*\{[^}]+\}", html, re.DOTALL)
add_combined = "\n".join(add_blocks)
if not add_blocks:
    fail("[6] blok .comp-add-cell tidak ditemukan")
else:
    if "transparent" not in add_combined:
        fail("[6] .comp-add-cell harus border transparent (subtle)")
    if "var(--bg-soft)" not in add_combined:
        fail("[6] .comp-add-cell harus bg var(--bg-soft)")
    if "0.7" not in add_combined:
        fail("[6] .comp-add-cell harus opacity 0.7")
    # hover harus accent solid
    hover_blocks = re.findall(r"\.comp-add-cell:hover\s*\{[^}]+\}", css, re.DOTALL) + re.findall(r"\.comp-add-cell:hover\s*\{[^}]+\}", html, re.DOTALL)
    hover_comb = "\n".join(hover_blocks)
    if "var(--accent)" not in hover_comb or "solid" not in hover_comb:
        fail("[6] .comp-add-cell:hover harus accent solid")
    # font-size lebih kecil dari 0.72 (harus ada dan lebih kecil)
    # cek ada font-size di add_combined
    m = re.search(r"font-size\s*:\s*([0-9.]+)rem", add_combined)
    if m:
        try:
            sz = float(m.group(1))
            if sz >= 0.72:
                fail(f"[6] text '＋ Model' harus lebih kecil dari 0.72rem (sekarang {sz}rem)")
        except: pass
    else:
        fail("[6] .comp-add-cell harus punya font-size lebih kecil")
# cek text "＋ Model" atau "＋" ada di html
if "＋ Model" not in html and "＋" not in html:
    fail("[6] text tombol ghost harus '＋ Model' (bukan '+ Tambah Model')")

# final report
if fails:
    print("GAGAL — cek W1 tidak lolos:")
    for f in fails:
        print(" -", f)
    print(f"\nTotal gagal: {len(fails)}")
    sys.exit(1)
else:
    print("LOLOS — semua cek W1 P0 terpenuhi")
    sys.exit(0)
