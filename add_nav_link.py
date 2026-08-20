import os

files = ['site/induksi.html', 'site/rotasi.html', 'site/proses.html', 'site/galeri.html', 'site/file.html']

for f in files:
    with open(f, 'r', encoding='utf-8') as fp:
        content = fp.read()
    # Add kompetitor after produk
    content = content.replace(
        '<a href="produk.html">Produk</a>',
        '<a href="produk.html">Produk</a>\n      <a href="kompetitor.html">Kompetitor</a>'
    )
    with open(f, 'w', encoding='utf-8') as fp:
        fp.write(content)
    print(f"Updated {f}")

print("Done!")