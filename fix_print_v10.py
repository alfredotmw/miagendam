import re

file_path = r'c:\Users\alfre\OneDrive\Documentos\Agenda\agendas_medicas\static\historial_turnos.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# STRATEGY V10: LARGE BOTTOM MARGIN RESERVATION
# User suggests: "put the footer at so many cm from the end, like a margin".
# We will increase the bottom margin of the page significantly (e.g. 3cm).
# We will keep the footer position:fixed bottom:0.
# Standard browser behavior places fixed elements at the bottom of the PAGE AREA (defined by margins).
# So formatting:
#   Paper Edge
#   |
#   | (3cm Margin) -> Footer sits here, at the bottom of the "content box" boundary
#   |
#   Content text

# 1. UPDATE @PAGE MARGIN
# Find: margin: 1cm;
# Replace with: margin: 1cm 1cm 3cm 1cm;

# Note: The file currently has:
# @page {
#     size: A4;
#     margin: 1cm;
# }

page_css_pattern = r'@page\s*\{[^}]*margin:\s*1cm;[^}]*\}'
new_page_css = """@page {
                size: A4;
                margin: 1cm 1cm 3.5cm 1cm; /* Large bottom margin to reserve space for footer */
            }"""

# Use a broader regex to find the @page block if exact match fails
# We look for "margin: 1cm" inside @page
content = re.sub(r'margin:\s*1cm;', 'margin: 1cm 1cm 3.5cm 1cm;', content)

# 2. UPDATE FOOTER POSITIONING
# It's currently bottom: 0.
# We might want to adjust it slightly if it feels too high relative to the margin line,
# but bottom:0 refers to the margin line.
# Let's ensure padding is clean.

# We also check if we need to remove the "footer-space" spacer we restored in V9.
# If we use margins, we don't necessarily need the spacer div in tfoot, but it doesn't hurt.
# However, if tfoot is present, it might still render *above* the margin?
# In V9 we restored tfoot with a spacer.
# If we use large margins + fixed footer, the tfoot spacer will consume content space.
# That's fine, it prevents overlap.

# Crucially, we must ensure the footer has z-index.
# The previous script set z-index: 999999.

print("Updated page margins to reserve footer space.")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
