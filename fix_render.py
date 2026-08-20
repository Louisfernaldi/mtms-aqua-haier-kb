with open('site/js/produk.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Lines 574-587 are corrupted
# 574: var modalEl = ...
# 575: if (modalEl) ...
# 577:       }
# 578:         if (modalEl) ... (DUPLICATE)
# 579:         document.body...
# 580:        {  (extra brace)
# 581-587: render function body (without function declaration)
# 587:       } (extra close)

# Replace lines 573-587 with correct code
new_lines = lines[:573] + [
    '\n',
    '      render();\n',
    '      initEditor(items, host);\n',
    '    })\n',
    '    .catch(function (err) {\n',
    '      console.error("[MTMS] renderKatalog error:", err && err.message, err && err.stack);\n',
    '      host.innerHTML = \'<p class="sec-sub">Katalog gagal dimuat.</p>\';\n',
    '    });\n',
    '}\n'
] + lines[592:]  # skip the corrupted lines and catch block (which we already have)

with open('site/js/produk.js', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
print('Fixed!')