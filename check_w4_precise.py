#!/usr/bin/env python3
import re, pathlib, sys
root = pathlib.Path(__file__).parent
index = (root/"site"/"index.html").read_text(encoding="utf-8")
css = (root/"site"/"css"/"style.css").read_text(encoding="utf-8")
galeri = (root/"site"/"galeri.html").read_text(encoding="utf-8")
komp = (root/"site"/"kompetitor.html").read_text(encoding="utf-8")
theme = (root/"site"/"js"/"theme.js").read_text(encoding="utf-8") if (root/"site"/"js"/"theme.js").exists() else ""
combined = css + "\n" + komp
def norm(s): return re.sub(r'\s+','',s)
css_n = norm(css)
komp_n = norm(komp)
combined_n = norm(combined)
# helper extract blocks
def extract_blocks(pattern,s): return re.findall(pattern,s,flags=re.S)
fails=[]
def need(c,msg):
    if not c:
        fails.append(msg)
        print(f"FAIL: {msg}")
    else:
        print(f"OK: {msg}")

# 1
need('class="nav-toggle"' in index, "1a button nav-toggle ada")
need('aria-label="Menu"' in index, "1b aria-label Menu")
need('nav-toggle' in index and 'nav-links' in index and index.index('nav-toggle') < index.index('nav-links'), "1c posisi toggle sebelum nav-links")
# scope nav-links block
nav_blocks = re.findall(r'\.nav-links\s*\{[^}]+\}', css, re.S)
nav_text = " ".join(nav_blocks) if nav_blocks else ""
need('overflow-x' in nav_text and 'auto' in nav_text, "1d nav-links overflow-x:auto")
need('flex-wrap' in nav_text and 'nowrap' in nav_text, "1e nav-links flex-wrap:nowrap")
need('scrollbar-width' in nav_text and 'none' in nav_text, "1f nav-links scrollbar-width:none")
need('-webkit-overflow-scrolling' in nav_text and 'touch' in nav_text, "1g nav-links -webkit-overflow-scrolling:touch")
need('.nav-toggle' in css, "1h css .nav-toggle ada")
# find nav-toggle block contains display:none
nt_blocks = re.findall(r'\.nav-toggle\s*\{[^}]+\}', css, re.S)
need(any('display' in b and 'none' in b for b in nt_blocks), "1i nav-toggle display:none")
need('max-width' in css and '640px' in css, "1j media 640 ada")
# nav-links.open inside media
need('.nav-links.open' in css_n and 'display:flex' in css_n, "1k nav-links.open display:flex")
# drawer style: look for @media block containing position:fixed top:58px
media_blocks = re.findall(r'@media[^{]*640px[^{]*\{(.+?)\n\}', css, re.S)  # rough
# better: search for position:fixed near nav-links
drawer_ok = False
# look for .nav-links inside @media 640 with position fixed
for m in re.finditer(r'@media[^{]*640px[^{]*\{([\s\S]*?)\n\}', css):
    block = m.group(1)
    if '.nav-links' in block and 'position:fixed' in norm(block) and 'top:58px' in norm(block):
        drawer_ok=True
if not drawer_ok:
    # fallback: check combined for drawer pattern
    drawer_ok = ('.nav-links.open' in css_n and 'position:fixed' in css_n and 'top:58px' in css_n)
need(drawer_ok, "1l drawer fixed top58")
need('width:40px' in css_n and 'height:40px' in css_n and '.nav-toggle' in css, "1m tap 40px nav-toggle 40x40")
need('classList.toggle' in index or 'classList.toggle' in theme, "1n JS toggle classList.toggle")
need('nav-toggle' in index or 'nav-toggle' in theme, "1o toggle ref")

#2
need('gallery-skeleton' in css or 'gallery-skeleton' in galeri, "2a gallery-skeleton")
need('.skel' in css, "2b .skel")
need('shimmer' in css, "2c shimmer")
need('background-size:200%' in css_n, "2d bg-size 200%")
need('animation:shimmer' in css_n, "2e animation shimmer")
need('@keyframesshimmer' in css_n, "2f keyframes shimmer")
need('skeleton' in galeri.lower() or 'gallery-skeleton' in galeri or 'skel' in galeri, "2g galeri skeleton placeholder")
need('Foto belum dimuat' in galeri or 'tarik ulang' in galeri.lower() or 'Memuat foto' in galeri, "2h galeri teks")

#3
need('.bp img' in css, "3a .bp img")
bp_blocks = re.findall(r'\.bp img\s*\{[^}]+\}', css, re.S)
bp_text = " ".join(bp_blocks)
need('height:200px' in norm(bp_text) or 'height:200px' in css_n, "3b height 200px")
need('aspect-ratio:16/10' in norm(bp_text) or 'aspect-ratio:16/10' in css_n, "3c aspect-ratio 16/10")
need('object-fit:cover' in norm(bp_text), "3d object-fit cover")
need('object-position:center' in norm(bp_text), "3e object-position center")
need('height:160px' in css_n, "3f 160px mobile")
need('background:var(--bg-soft)' in norm(bp_text), "3g bg soft")

#4
comp_n = norm(combined)
need('.comp-edit-cardlabel' in comp_n, "4a label")
need('margin:12px06px' in comp_n, "4b margin12 0 6")
need('padding:10px12px' in comp_n, "4c padding10 12")
need('font-size:0.95rem' in comp_n, "4d font 0.95")
need('border-top:1pxsolidvar(--border)' in comp_n, "4e border-top")
need('padding-top:12px' in comp_n, "4f padding-top12")
need('margin-top:16px' in comp_n, "4g margin16")
need('.edit-actions' in combined, "4h edit-actions")

#5 backdrop
# check each overlay has rgba and blur
need('rgba(6,16,22,.64)' in css_n or 'rgba(6,16,22,0.64)' in css_n, "5a backdrop rgba .64")
need('backdrop-filter:blur(4px)' in css_n, "5b blur4")
# z-index check specifics
# extract search-overlay block
so = re.findall(r'\.search-overlay\s*\{[^}]+\}', css, re.S)
pk = re.findall(r'\.pk-modal[^{]*\{[^}]+\}', css, re.S)
z_s = None; z_p=None
if so:
    m=re.search(r'z-index\s*:\s*(\d+)', so[0])
    if m: z_s=int(m.group(1))
if pk:
    # first pk-modal block
    for b in pk:
        m=re.search(r'z-index\s*:\s*(\d+)', b)
        if m:
            z_p=int(m.group(1)); break
need(z_s==120, f"5c search z-index 120 (got {z_s})")
need('.comp-edit-overlay' in combined, "5d comp-edit-overlay")
need('.search-overlay' in css, "5e search-overlay")
need('.pk-modal' in css, "5f pk-modal")
need('.lightbox' in css, "5g lightbox")
need(z_s is not None and z_p is not None and z_s>z_p, f"5h search {z_s} > pk {z_p}")
# also check comp-edit-overlay backdrop
ce = re.findall(r'\.comp-edit-overlay\s*\{[^}]+\}', combined, re.S)
need(any(('rgba(6,16,22,.64)' in norm(b) or 'rgba(6,16,22,0.64)' in norm(b)) for b in ce), "5i comp-edit-overlay backdrop .64")
# search-overlay backdrop
need(any(('rgba(6,16,22,.64)' in norm(b) or 'rgba(6,16,22,0.64)' in norm(b)) for b in so), "5j search backdrop rgba .64")
# lightbox backdrop
lb = re.findall(r'\.lightbox\s*\{[^}]+\}', css, re.S)
need(any(('rgba(6,16,22,.64)' in norm(b) or 'rgba(6,16,22,0.64)' in norm(b)) for b in lb), "5k lightbox backdrop .64")
# also check pk-modal and pk-edit-overlay backlog .64
pk_all = re.findall(r'\.pk-modal[^{]*\{[^}]+\}', css, re.S) + re.findall(r'\.pk-edit-overlay\s*\{[^}]+\}', css, re.S)
need(any(('rgba(6,16,22,.64)' in norm(b) or 'rgba(6,16,22,0.64)' in norm(b)) for b in pk_all), "5l pk-modal/pk-edit-overlay backdrop .64")
need('backdrop-filter:blur(4px)' in css_n, "5m blur 4px generic")

#6
need('font-size:0.85rem' in comp_n, "6a label 0.85")
need('font-weight:600' in comp_n, "6b 600")
need('line-height:1.5' in comp_n, "6c 1.5")
need('outline:2pxsolidvar(--accent)' in comp_n, "6d outline 2px")
need('outline-offset:2px' in comp_n, "6e offset2")
need('border-color:var(--accent)' in comp_n, "6f border-color")
need(':focus' in combined, "6g focus")

#7
need('.comp-row-actionsbutton' in comp_n, "7a row-actions button")
need('font-size:0.75rem' in comp_n, "7b 0.75")
need('padding:6px12px' in comp_n, "7c padding6 12")
need('min-height:32px' in comp_n, "7d min32")

if fails:
    print(f"\nGAGAL {len(fails)}")
    for f in fails: print(" -",f)
    sys.exit(1)
else:
    print("\nSEMUA LULUS")
    sys.exit(0)
