import re

file_path = r'c:\Users\alfre\OneDrive\Documentos\Agenda\agendas_medicas\static\historial_turnos.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# STRATEGY V11: STANDARD PAGE MARGINS + BODY PADDING CUSHION
# The previous attempt (large @page margin) clipped the footer.
# User wants footer at "so many cm from end" (visual margin).
# Solution:
# 1. @page margin: 1cm (Standard, keeps footer valid/printable).
# 2. Body padding-bottom: 3cm (Forces content to stop early).
# 3. Footer bottom: 0 (Sits in the padded area, safe from content).

# 1. REVERT @PAGE MARGIN
# Find: margin: 1cm 1cm 3.5cm 1cm;
# Replace with: margin: 1cm;
content = content.replace('margin: 1cm 1cm 3.5cm 1cm;', 'margin: 1cm;')

# 2. ADD BODY PADDING
# Find: body { ... padding: 0 !important; ... }
# We need to change this padding-bottom for PRINT execution.
# Current CSS:
# html, body {
#     margin: 0 !important;
#     padding: 0 !important;
#     background: white !important;
# }
# We'll allow specific padding bottom.

body_css = """html, body {
                margin: 0 !important;
                padding: 0 !important;
                padding-bottom: 2cm !important; /* Reserve 2cm at bottom for footer */
                background: white !important;
                height: 100%; /* Ensure body fills page for footer positioning */
            }"""

# Regex to replace the html, body block inside @media print
# It matches broadly, so be careful.
# Alternatively, we just inject the padding rule or redefine it.
# Let's redefine it cleanly.

# Search for the specific block
# html, body {\s*margin: 0 !important;\s*padding: 0 !important;\s*background: white !important;\s*}
# We might match loosely.
regex_body = r'html,\s*body\s*\{\s*margin:\s*0\s*!important;\s*padding:\s*0\s*!important;\s*background:\s*white\s*!important;\s*\}'

if re.search(regex_body, content):
    content = re.sub(regex_body, body_css, content)
    print("Updated body padding for print.")
else:
    # Fallback: Just insert a new rule after @media print {
    print("Could not find exact body rule match, injecting new one.")
    content = content.replace('@media print {', '@media print {\n            html, body { padding-bottom: 25mm !important; height: auto !important; }')
    # Note: 25mm = 2.5cm safe zone.

# 3. VERIFY FOOTER CSS
# Ensure footer is fixed bottom 0.
# The previous script (V9/V10) kept it fixed. We just need to ensure it wasn't broken.
# .print-footer-content { position: fixed; bottom: 0; ... }
# Ensure no 'display: none' snuck in.

# We will FORCE standard safe CSS for the footer just in case.
footer_css_force = """
            .print-footer-content {
                position: fixed;
                bottom: 0px !important;
                left: 0px !important;
                width: 100%;
                background: white;
                border-top: 1px solid #ccc;
                display: block !important;
                z-index: 2147483647; /* Max Z-Index */
                padding-bottom: 5px;
            }
"""
content = re.sub(r'\.print-footer-content\s*\{[^}]*\}', footer_css_force.strip(), content)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
