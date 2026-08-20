with open('site/js/produk.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Remove duplicate block (lines 578-586 approximately)
# Find the pattern: blank line, then duplicate modalEl block, then blank line, then function render
new_lines = []
i = 0
skip = False
while i < len(lines):
    if i >= 577 and i <= 586:
        # Check if this is the duplicate block
        if 'if (modalEl) modalEl.classList.add("open");' in lines[i] and skip:
            # Skip until we hit 'function render'
            if 'function render()' in lines[i]:
                skip = False
            i += 1
            continue
        elif 'if (modalEl) modalEl.classList.add("open");' in lines[i]:
            skip = True
            i += 1
            continue
    if not skip:
        new_lines.append(lines[i])
    i += 1

with open('site/js/produk.js', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
print('Fixed!')