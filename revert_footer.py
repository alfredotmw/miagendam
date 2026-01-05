import re

file_path = 'static/historial_turnos.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Extract Base64 Source from the current tfoot
match = re.search(r'<img src="(data:image/jpeg;base64,[^"]+)"', content)
if not match:
    # Just in case, try to find it anywhere
    print("Could not find base64 image source in tfoot. Searching entire file...")
    match = re.search(r'src="(data:image/jpeg;base64,[^"]+)"', content)

if not match:
    print("Fatal: Could not find base64 string.")
    exit(1)

base64_src = match.group(1)

# 2. Remove the tfoot content (clean up table)
# We can just empty the footer-space div
tfoot_pattern = r'(<div class="footer-space"[^>]*>)([\s\S]*?)(</div>)'
content = re.sub(tfoot_pattern, r'\1\3', content)

# 3. Insert the Fixed Footer div at the end of body
# We want it strictly smaller, so max-width: 60%
fixed_footer_html = f"""
    <div class="print-footer-content">
        <div style="width: 100%; text-align: center; background: white; padding-top: 5px;">
            <img src="{base64_src}" alt="Footer" style="max-width: 65%; height: auto; display: inline-block;">
        </div>
    </div>
</body>"""

content = content.replace('</body>', fixed_footer_html)

# 4. Update CSS for .print-footer-content
# We need to make sure the CSS exists and is correct for FIXED positioning
# I'll replace the existing CSS block for .print-footer-content or append a fix if needed.
# Let's rewrite the CSS rule to be sure.
css_rule = """
            .print-footer-content {
                display: block !important;
                position: fixed;
                bottom: 0 !important;
                top: auto !important;
                left: 0;
                right: 0;
                width: 100%;
                background: white;
                z-index: 2147483647;
                padding-bottom: 0;
                height: auto !important;
                border: none !important;
                visibility: visible !important;
                opacity: 1 !important;
            }
"""
# Search for existing rule to replace
css_pattern = r'\.print-footer-content\s*\{[^}]+\}'
if re.search(css_pattern, content):
    content = re.sub(css_pattern, css_rule.strip(), content)
else:
    # If not found, inject it into @media print
    print("CSS rule not found to replace. Injecting...")
    content = content.replace('/* 7. FIXED FOOTER */', '/* 7. FIXED FOOTER */\n' + css_rule)

# 5. Ensure margins are set to reserve space
# User said "hoja 2 no sale como pie de pagina" -> It needs to be at bottom.
# Fixed pos handles that. Margin bottom reserves space so content doesn't overlap.
# Let's set margin-bottom back to 30mm to be safe and clear.
content = content.replace('margin-bottom: 10mm;', 'margin-bottom: 30mm;')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Reverted to fixed footer with smaller size.")
