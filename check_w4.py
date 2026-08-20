#!/usr/bin/env python3
# check_w4.py — gerbang P0 W4 index+komponen
# JANGAN DIEDIT CODEX — ini alat ukur.
import re, pathlib, sys

root = pathlib.Path(__file__).parent
index = (root/"site"/"index.html").read_text(encoding="utf-8")
css = (root/"site"/"css"/"style.css").read_text(encoding="utf-8")
galeri = (root/"site"/"galeri.html").read_text(encoding="utf-8")
komp = (root/"site"/"kompetitor.html").read_text(encoding="utf-8")

fails = []
combined = css + "\n" + komp

def norm(s): return re.sub(r'\s+', '', s)

css_n = norm(css)
komp_n = norm(komp)
combined_n = norm(combined)
galeri_n = norm(galeri)
index_n = norm(index)

def need(cond, msg):
    if not cond:
        fails.append(msg)
        print(f"FAIL: {msg}")
    else:
        print(f"OK: {msg}")

# 1 — nav flex-wrap + drawer
need('class="nav-toggle"' in index, "1a index.html ada button .nav-toggle")
need('aria-label="Menu"' in index or 'aria-label="menu"' in index.lower(), "1b nav-toggle aria-label Menu")
# check nav-toggle before nav-links order
if 'class="nav-toggle"' in index:
    need(index.index('nav-toggle') < index.index('nav-links'), "1c nav-toggle sebelum nav-links")
else:
    need(False, "1c nav-toggle sebelum nav-links (toggle belum ada)")
need('overflow-x:auto' in css_n, "1d css .nav-links overflow-x:auto")
need('flex-wrap:nowrap' in css_n, "1e css flex-wrap:nowrap ada")
need('scrollbar-width:none' in css_n, "1f scrollbar-width:none")
need('-webkit-overflow-scrolling:touch' in norm(css), "1g -webkit-overflow-scrolling:touch")
need('.nav-toggle' in css, "1h css .nav-toggle ada")
need('.nav-toggle' in css and 'display:none' in css_n, "1i .nav-toggle display:none (cek ada)")
# drawer @media 640
need('@media' in css and '640px' in css, "1j media max-width 640 ada")
need('.nav-links.open' in css_n and 'display:flex' in css_n, "1k .nav-links.open display:flex")
need('position:fixed' in css_n and 'top:58px' in css_n, "1l drawer position fixed top 58px")
need('40px' in css, "1m drawer tap 40px width/height")
# JS toggle
theme = (root/"site"/"js"/"theme.js").read_text(encoding="utf-8") if (root/"site"/"js"/"theme.js").exists() else ""
need('classList.toggle' in index or 'classList.toggle' in theme or 'classList.toggle' in combined, "1n JS toggle classList.toggle open ada")
need('nav-toggle' in index or 'nav-toggle' in theme, "1o toggle JS reference")

# 2 — skeleton shimmer
need('gallery-skeleton' in css or 'gallery-skeleton' in galeri, "2a gallery-skeleton class ada")
need('.skel' in css, "2b .skel ada")
need('shimmer' in css, "2c shimmer animation ada")
need('background-size:200%' in css_n, "2d background-size 200%")
need('animation:shimmer' in css_n, "2e animation shimmer")
need('@keyframesshimmer' in css_n, "2f keyframes shimmer")
# galeri.html placeholder
need('Memuat' in galeri or 'skeleton' in galeri.lower() or 'skel' in galeri, "2g galeri.html placeholder / skeleton ada")
need('Foto belum dimuat' in galeri or 'tarik ulang' in galeri.lower() or 'Memuat foto' in galeri, "2h galeri teks foto belum dimuat / memuat foto")

# 3 — bp img 200px 16/10
need('.bp img' in css, "3a .bp img ada")
need('height:200px' in css_n, "3b .bp img height 200px")
need('aspect-ratio:16/10' in css_n, "3c aspect-ratio 16/10")
need('object-fit:cover' in css_n, "3d object-fit:cover")
need('object-position:center' in css_n, "3e object-position:center")
need('height:160px' in css_n, "3f media 640 height 160px")
need('background:var(--bg-soft)' in css_n, "3g background var(--bg-soft)")

# 4 — edit overlay gap12
need('.comp-edit-cardlabel' in combined_n, "4a .comp-edit-card label ada")
need('margin:12px06px' in combined_n, "4b label margin 12px 0 6px")
need('padding:10px12px' in combined_n, "4c input padding 10px 12px")
need('font-size:0.95rem' in css_n, "4d font 0.95rem (check css)")
need('border-top:1pxsolidvar(--border)' in combined_n, "4e border-top seksi")
need('padding-top:12px' in combined_n, "4f padding-top 12px")
need('margin-top:16px' in combined_n, "4g margin-top 16px")
need('.edit-actions' in combined, "4h .edit-actions ada")

# 5 — backdrop konsisten
need('rgba(6,16,22,.64)' in css_n or 'rgba(6,16,22,0.64)' in css_n, "5a backdrop rgba(6,16,22,.64) ada")
need('backdrop-filter:blur(4px)' in css_n, "5b backdrop-filter blur 4px")
need('z-index:120' in combined_n, "5c search-overlay z-index 120")
need('.comp-edit-overlay' in combined, "5d .comp-edit-overlay ada")
need('.search-overlay' in css, "5e .search-overlay ada")
need('.pk-modal' in css, "5f .pk-modal ada")
need('.lightbox' in css, "5g .lightbox ada")

# search z-index > pk-modal ?
z_search = None
z_pk = None
# search in combined (inline may override)
for src in [css, komp]:
    m = re.search(r'\.search-overlay[^}]*z-index\s*:\s*(\d+)', src)
    if m: z_search = int(m.group(1))
    m = re.search(r'\.pk-modal[^}]*z-index\s*:\s*(\d+)', src)
    if m: z_pk = int(m.group(1))
    m2 = re.search(r'\.pk-modal\s*\{[^}]*z-index\s*:\s*(\d+)', src, re.S)
    if m2: z_pk = int(m2.group(1))
    m3 = re.search(r'\.search-overlay\s*\{[^}]*z-index\s*:\s*(\d+)', src, re.S)
    if m3: z_search = int(m3.group(1))
# fallback global search: find any highest z-index mention for search-overlay vs pk-modal
if z_search is None:
    mm = re.findall(r'z-index\s*:\s*(\d+)', css)
    # try approximate: search-overlay should be 120
    z_search = 120 if '120' in css else None
need(z_search is not None and z_pk is not None and z_search > z_pk, f"5h z-index search ({z_search}) > pk-modal ({z_pk})")

# 6 — label 0.85 + focus ring 2px
need('font-size:0.85rem' in combined_n, "6a label 0.85rem")
need('font-weight:600' in combined_n, "6b font-weight 600")
need('line-height:1.5' in combined_n, "6c line-height 1.5")
need('outline:2pxsolidvar(--accent)' in combined_n, "6d focus ring 2px accent")
need('outline-offset:2px' in combined_n, "6e outline-offset 2px")
need('border-color:var(--accent)' in combined_n, "6f border-color accent on focus")
need(':focus' in combined, "6g :focus selector ada")

# 7 — comp-row-actions 0.75rem 6px12px min-height32
need('.comp-row-actionsbutton' in combined_n, "7a comp-row-actions button ada")
need('font-size:0.75rem' in combined_n, "7b font 0.75rem")
need('padding:6px12px' in combined_n, "7c padding 6px 12px")
need('min-height:32px' in combined_n, "7d min-height 32px")

# extra: no console error hint — check files exist
need((root/"site"/"index.html").exists(), "extra index exists")
need((root/"site"/"css"/"style.css").exists(), "extra style exists")

if fails:
    print(f"\n=== GAGAL {len(fails)} cek ===")
    for f in fails: print(" -", f)
    sys.exit(1)
else:
    print("\n=== SEMUA CEK LULUS ===")
    sys.exit(0)
