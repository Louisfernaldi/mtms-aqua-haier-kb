with open('site/js/produk.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

start = None
for i, line in enumerate(lines):
    if 'TOP tabs: Detail / Perbandingan' in line:
        start = i
        break

end = 657

print('start:', start, 'end:', end)

if start is not None:
    new_lines = lines[:start] + [
        '\n',
        '        var modalEl = document.querySelector(".pk-modal");\n',
        '        if (modalEl) modalEl.classList.add("open");\n',
        '        document.body.style.overflow = "hidden";\n',
        '      }\n'
    ] + lines[659:]
    with open('site/js/produk.js', 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    print('Done!')
else:
    print('Could not find start')