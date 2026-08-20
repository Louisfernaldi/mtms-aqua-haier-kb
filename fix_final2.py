with open('site/js/produk.js', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the clean end point and the EDITOR section
clean_end = content.find('      render();\n      initEditor(items, host);\n    })\n    .catch(function (err) {\n      console.error("[MTMS] renderKatalog error:", err && err.message, err && err.stack);\n      host.innerHTML = \'<p class="sec-sub">Katalog gagal dimuat.</p>\';\n    });\n}')

print('Clean end at:', clean_end)

if clean_end != -1:
    editor_idx = content.find('// ================= EDITOR')
    # Keep everything up to clean_end + the closing '}' of the function
    # Then skip the duplicate and go to EDITOR
    new_content = content[:clean_end + 1] + '\n' + content[content.find('// ================= EDITOR'):]
    with open('site/js/produk.js', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print('Fixed!')
else:
    print('Clean end not found, trying alternative...')
    # Find the last clean '}' before the duplicate
    idx = content.rfind('    })\n    .catch(function (err) {\n      console.error("[MTMS] renderKatalog error:", err && err.message, err && err.stack);\n      host.innerHTML = \'<p class="sec-sub">Katalog gagal dimuat.</p>\';\n    });\n}')
    if idx != -1:
        print('Found at:', idx)
        editor_idx = content.find('// ================= EDITOR')
        new_content = content[:idx + 1] + '\n' + content[editor_idx:]
        with open('site/js/produk.js', 'w', encoding='utf-8') as f:
            f.write(new_content)
        print('Fixed with alternative!')
    else:
        print('Not found')