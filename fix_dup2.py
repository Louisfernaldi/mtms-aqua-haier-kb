with open('site/js/produk.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Remove duplicate lines 583-586 (0-indexed: 582-585)
new_lines = lines[:582] + lines[586:]
with open('site/js/produk.js', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
print('Fixed!')