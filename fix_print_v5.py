import re

file_path = r'c:\Users\alfre\OneDrive\Documentos\Agenda\agendas_medicas\static\historial_turnos.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. FIX PAGINATION: Inject counter-increment into @page
# Current:
#             @page {
#                 size: A4;
#                 margin: 0; 
#             }
# Target:
#             @page {
#                 size: A4;
#                 margin: 0;
#                 counter-increment: page;
#             }

if 'counter-increment: page' not in content:
    content = content.replace(
        'size: A4;\n                margin: 0;', 
        'size: A4;\n                margin: 0;\n                counter-increment: page;'
    )
    print("Injected counter-increment: page")

# 2. FIX FOOTER VISIBILITY
# The user says it "doesn't come out". With margin: 0 on page, bottom: 0 on fixed element is at the very edge.
# Most home printers cannot print the last 5-10mm.
# We need to move the footer visual content UP.
# Currently .print-footer-content has:
#                 bottom: 0px;
#                 height: 50px;
#                 padding: 10px 1cm;
# This means the content starts 10px from top of footer. Footer is 50px tall.
# So content is in the band 0-40px from bottom.
# If printer clips bottom 10mm (approx 38px), almost the whole footer is gone!
# WE MUST INCREASE HEIGHT AND PADDING.
# Let's make height 80px. Position bottom 0. Padding-bottom 30px (approx 8mm). 
# This pushes text up.

# Find the .print-footer-content css block again.
# We can use regex replacement on the height and padding.

# Regex to find height: 50px inside .print-footer-content
# This is tricky with regex context.
# Let's replace the entire CSS class definition again to be sure.

new_footer_css = """
            .print-footer-content {
                position: fixed;
                bottom: 0px;
                left: 0;
                width: 100%;
                height: 90px; /* INCREASED HEIGHT */
                background: white;
                /* border-top: 1px solid #ccc;  Optional, maybe remove if it looks weird floating */
                
                display: block !important;
                
                /* PADDING ADJUSTMENT */
                /* Top 10px, Side 1cm, Bottom 30px to clear printer margins */
                padding: 10px 1cm 35px 1cm; 
                box-sizing: border-box;
                z-index: 999999;
            }
"""

# Replace the specific block we wrote last time
# We look for .print-footer-content { ... }
# Note: we need to match broadly enough.
pattern = r'\.print-footer-content\s*\{[^}]*z-index:\s*999999;\s*\}'
# The previous write had z-index: 999999 inside.
match = re.search(pattern, content, re.DOTALL)
if match:
    content = content.replace(match.group(0), new_footer_css.strip())
    print("Replaced footer CSS with taller safe-area version.")
else:
    print("Could not find footer CSS block to replace via regex (trying manual string search fallback)")
    # Fallback: looks for the string "height: 50px;" inside print CSS context?
    # Or just Replace the whole @media print block? No, that's risky if I mess up other parts.
    # Let's try to find the previous known css signature
    old_sig = "height: 50px;"
    if content.count(old_sig) == 1:
        # Assuming only one place has height: 50px (the footer)
        # Verify it's near .print-footer-content
        pass 
    
    # Let's try to overwrite the @media print .print-footer-content block by finding its start.
    start_str = ".print-footer-content {"
    idx = content.find(start_str)
    if idx != -1:
        # Find closing brace
        end_idx = content.find("}", idx)
        if end_idx != -1:
            # Replace
            content = content[:idx] + new_footer_css.strip() + content[end_idx+1:]
            print("Replaced footer CSS by finding braces.")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
