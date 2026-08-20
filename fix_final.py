with open('site/js/produk.js', 'r', encoding='utf-8') as f:
    content = f.read()

# Find first 'var modalEl'
first_var = content.find('var modalEl = document.querySelector')
print('First var at:', first_var)

# Find the end of first block (the '}' that closes the openModal function)
# Look for the pattern: '      }\n' after first_var
first_block_end = content.find('      }\n', first_var)
print('First block end at:', first_block_end)

# Find second 'function render()'
first_render = content.find('function render()')
second_render = content.find('function render()', first_render + 1)
print('Second render at:', second_render)

# Rebuild: keep up to first block end, then add the rest from second render
# But we need to keep the closing of openModal function
# The openModal function ends at first '      }\n' after 'var modalEl'
# Then there's a duplicate block, then 'function render()'

# Let's find the actual end of openModal function
# It should be '      }\n' followed by blank line then 'function render()'

# Find the pattern: '      }\n\n      function render()'
import re
pattern = r'      }\n\n      function render\(\)'
match = re.search(pattern, content)
if match:
    print('Pattern found at:', match.start())
    # Keep everything up to the '      }\n' before function render
    keep_end = match.start() + 6  # include '      }\n'
    new_content = content[:keep_end] + content[match.end():]
    with open('site/js/produk.js', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print('Fixed using regex!')
else:
    print('Pattern not found, trying alternative...')
    # Alternative: find all '      }\n' after first_var
    pos = first_var
    while True:
        next_brace = content.find('      }\n', pos + 1)
        if next_brace == -1:
            break
        # Check if followed by blank line and function render
        if content[next_brace + 6:next_brace + 20].startswith('\n      function render()'):
            print('Found correct end at:', next_brace)
            new_content = content[:next_brace + 6] + content[next_brace + 6 + 2:]  # skip blank line
            with open('site/js/produk.js', 'w', encoding='utf-8') as f:
                f.write(new_content)
            print('Fixed using loop!')
            break
        pos = next_brace