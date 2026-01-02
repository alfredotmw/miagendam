import re
import os

file_path = r'c:\Users\alfre\OneDrive\Documentos\Agenda\agendas_medicas\static\historial_turnos.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Modify CSS to fix Page 0 and Footer Visibility
# - Add counter-reset: page 0; to html/body
# - Change body > #print-footer to #print-footer
# - Ensure @page has counter-increment

# Fix basic body/html rule for counter-reset
if 'counter-reset: page' not in content:
    # Add it to the main print body rule
    content = content.replace(
        'print-color-adjust: exact;', 
        'print-color-adjust: exact;\n                counter-reset: page 0;'
    )

# Relax the footer selector
content = content.replace('body>#print-footer', '#print-footer')

# 2. Update the HTML of the footer
# - Remove style="display: none;" to avoid specificity wars
# - Use the simple text content
# - Ensure z-index is super high

old_footer_tag = '<div id="print-footer" class="print-footer-content" style="display: none;">'
new_footer_tag = '<div id="print-footer" class="print-footer-content">' # Removed style="display: none;"

content = content.replace(old_footer_tag, new_footer_tag)

# Update the content to the simple text version if not already (it should be from v2, but forcing safe update)
# We match the inner content we want.
target_text = "San Martín Nº 2473"
if target_text not in content:
    # If for some reason v2 didn't apply the text, we do a regex replace of the footer block again.
    # This is a fallback.
    print("Target text not found, attempting regex replacement of footer block.")
    footer_regex = r'(<div id="print-footer"[^>]*>.*?</div>\s*</div>)' 
    new_footer_html = """    <div id="print-footer" class="print-footer-content">
        <div style="display: flex; justify-content: center; align-items: center; height: 100%; width: 100%; text-align: center;">
            <p style="margin: 0; padding: 0; font-size: 10px; color: black !important; font-weight: bold;">
                San Martín Nº 2473 - whatsapp 3794684336 y Colombia Nº 1249 - whatsapp 3794409595. Corrientes. Instagram @oncologicocorrientes
            </p>
        </div>
    </div>"""
    
    # We look for the footer block again
    chunk_pattern = r'(<div id="print-footer".*?)(<!-- Sidebar -->)'
    match = re.search(chunk_pattern, content, re.DOTALL)
    if match:
        content = content.replace(match.group(1), new_footer_html + '\n\n    ')

# 3. Ensure the CSS for .print-footer-content has proper bottom placement and z-index
# We will use regex to update the CSS class definition
css_footer_regex = r'(\.print-footer-content\s*\{[^}]+\})'
new_css_footer = """
            .print-footer-content {
                position: fixed !important;
                bottom: 0px !important;
                left: 0 !important;
                width: 100% !important;
                height: 60px !important; /* Slightly reduced height to ensure it fits */
                background: white !important;
                border-top: 1px solid #ccc;
                display: block !important;
                padding: 10px 1cm !important;
                box-sizing: border-box;
                font-size: 9px;
                color: black !important;
                z-index: 2147483647 !important; /* Max z-index */
                overflow: visible !important;
            }"""

# Find the existing css block and replace it
# It starts with .print-footer-content { and ends with }
# The regex above is simple, let's use a more robust search if possible since we have unique class name
start_index = content.find('.print-footer-content {')
if start_index != -1:
    # Find matching closing brace
    brace_count = 0
    end_index = -1
    for i in range(start_index, len(content)):
        if content[i] == '{':
            brace_count += 1
        elif content[i] == '}':
            brace_count -= 1
            if brace_count == 0:
                end_index = i + 1
                break
    
    if end_index != -1:
        old_css = content[start_index:end_index]
        content = content.replace(old_css, new_css_footer.strip())
        print("Updated footer CSS.")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
