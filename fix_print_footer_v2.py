import re
import os

file_path = r'c:\Users\alfre\OneDrive\Documentos\Agenda\agendas_medicas\static\historial_turnos.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Remove counter-reset: page; from body rule
# Find:
#             body {
#                 background: white !important;
#                 ...
#                 counter-reset: page;
#             }
# We will just replace "counter-reset: page;" with empty string if found in that context.

if 'counter-reset: page;' in content:
    content = content.replace('counter-reset: page;', '')
    print("Removed counter-reset: page; from body.")
else:
    print("counter-reset: page; not found (might have been removed already).")


# 2. Replace Footer HTML with SIMPLE TEXT version
# Target: <div id="print-footer" ... </div> (the whole block)
# New content: Simple centered text div

new_footer_html = """    <!-- Footer moved OUT of the table for reliable fixed positioning -->
    <div id="print-footer" class="print-footer-content" style="display: none;">
        <div style="display: flex; justify-content: center; align-items: center; height: 100%; width: 100%; text-align: center;">
            <p style="margin: 0; padding: 0; font-size: 10px; color: black !important; font-weight: bold;">
                San Martín Nº 2473 - whatsapp 3794684336 y Colombia Nº 1249 - whatsapp 3794409595. Corrientes. Instagram @oncologicocorrientes
            </p>
        </div>
    </div>"""

# Regex to find the footer block again.
footer_regex = r'(<div id="print-footer"[^>]*>.*?</div>\s*</div>)' 
# Note: The previous footer bad a double nested div structure in some versions or table.
# Let's use a very broad matcher for the id until the next reliable tag start if possible, or just exact match the previous known state.
# The previous state from my last successful write was the flexbox div structure.

# Let's try to match the start of the footer div and capture everything until the Sidebar comment which follows it.
# Context:
#     </div>
# 
#     <!-- Sidebar -->

chunk_pattern = r'(<div id="print-footer".*?)(<!-- Sidebar -->)'
# Use DOTALL so . matches newlines
match = re.search(chunk_pattern, content, re.DOTALL)

if match:
    print("Found footer block ending at Sidebar comment.")
    # Replace the first group (the footer) with new content
    content = content.replace(match.group(1), new_footer_html + '\n\n    ')
    print("Footer replaced with simple text version.")
else:
    print("Could not find footer block via Sidebar lookahead regex. Trying generic div match.")
    # Fallback: try to find the specific ID and then the next closing div? No, that's risky with nested divs.
    # Let's look for the specific previous content if possible.
    # verification:
    if 'San Martín' in content and 'Colombia' in content:
        print("Old footer content found, but regex failed. Attempting brute force replacement of known identifiers.")
        # If we can identify a unique start and end line...
        pass

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
