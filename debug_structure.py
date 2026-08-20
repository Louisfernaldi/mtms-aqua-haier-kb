with open('site/js/produk.js', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the renderKatalog function end and fix it completely
# The issue is the Promise chain structure

# Let's find the loadKatalog call and rebuild from there cleanly
idx = content.find('loadKatalog()')
if idx == -1:
    print('loadKatalog not found')
else:
    print('Found loadKatalog at:', idx)
    # Find the end of renderKatalog function
    # It should end with '}' before '// ================= EDITOR'
    editor_idx = content.find('// ================= EDITOR')
    print('EDITOR section at:', editor_idx)
    
    # Extract the problematic section
    section = content[idx:editor_idx]
    print('Section length:', len(section))
    # Print last 500 chars
    print('Last 500 chars of section:')
    print(section[-500:])