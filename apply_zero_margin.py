import re

file_path = 'static/historial_turnos.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update @page rule to Zero Margin
# Regex to find @page block inside or outside media query
# We know it's inside @media print roughly.
# Let's replace the entire @page block.
page_rule_pattern = r'@page\s*\{[^}]+\}'
zero_margin_page = """@page {
                size: A4;
                margin: 0; /* DISABLE BROWSER MARGINS */
            }"""

if re.search(page_rule_pattern, content):
    content = re.sub(page_rule_pattern, zero_margin_page, content)
else:
    print("Warning: @page rule not found. Appending...")
    # This might be risky if we don't know where to insert, but usually it exists.

# 2. Update html/body styles for manual padding
# Pattern for html, body inside @media print
# Look for the block we edited before:
#             html,
#             body {
#                 margin: 0 !important;
#                 padding: 0 !important;
#                 background: white !important;
#             }
body_rule_pattern = r'html,\s*body\s*\{[^}]+\}'
padded_body_rule = """html,
            body {
                margin: 0 !important;
                /* Manual Padding: Top 10mm, Right 10mm, Bottom 40mm (for footer), Left 10mm */
                padding: 10mm 10mm 40mm 10mm !important;
                background: white !important;
                min-height: 100vh;
                box-sizing: border-box;
            }"""

if re.search(body_rule_pattern, content):
    content = re.sub(body_rule_pattern, padded_body_rule, content)

# 3. Update Footer Positioning
# Needs to be bottom: 0 relative to the PAGE (since margin is 0, this is the paper edge)
# But we probably want a tiny bit of breathing room/centering, or just exact placement.
# Let's stick to bottom: 0 and let the image's own whitespace/padding handle visual offset if any.
# Or better, bottom: 5mm for safety.
footer_rule_pattern = r'\.print-footer-content\s*\{[^}]+\}'
fixed_footer_rule = """.print-footer-content {
                display: block !important;
                position: fixed;
                bottom: 0 !important; /* Bottom of the physical page */
                left: 0;
                right: 0;
                width: 100%;
                background: transparent; /* Changed to transparent to avoid blocking if overlapping slightly */
                z-index: 2147483647;
                padding-bottom: 5mm; /* Visual padding from edge */
                height: auto !important;
                border: none !important;
                visibility: visible !important;
                opacity: 1 !important;
                text-align: center;
            }"""

if re.search(footer_rule_pattern, content):
    content = re.sub(footer_rule_pattern, fixed_footer_rule, content)

# 4. Remove previous margin-bottom adjustment hacks if any exist as standalone text
content = content.replace('margin-bottom: 30mm;', '') 

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Applied Zeron Margin CSS.")
