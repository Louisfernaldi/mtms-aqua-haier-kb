with open('site/js/produk.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find start and end
start = None
end = None
for i, line in enumerate(lines):
    if 'TOP tabs: Detail / Perbandingan' in line:
        start = i
    if 'var modalEl = document.querySelector' in line and i > 25900:
        end = i - 1  # line before modalEl
        break

print('start:', start, 'end:', end)
if start is not None and end is not None:
    # Replace lines[start:end+1] with new lines
    new_lines = lines[:start] + [
        '\n',
        '        var modalEl = document.querySelector(".pk-modal");\n',
        '        if (modalEl) modalEl.classList.add("open");\n',
        '        document.body.style.overflow = "hidden";\n',
        '      }\n'
    ] + lines[end+2:]
    with open('site/js/produk.js', 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    print('Done!')
else:
    print('Could not find bounds')