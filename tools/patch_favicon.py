import glob, io
for f in glob.glob(r"D:\AI\projects\mtms-aqua-haier-kb\site\*.html"):
    s = io.open(f, encoding="utf-8").read()
    if 'rel="icon"' not in s:
        s = s.replace(
            '<link rel="stylesheet" href="css/style.css">',
            '<link rel="stylesheet" href="css/style.css">\n<link rel="icon" href="data:,">',
        )
        io.open(f, "w", encoding="utf-8").write(s)
        print("patched", f)