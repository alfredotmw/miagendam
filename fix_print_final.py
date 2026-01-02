import re

file_path = r'c:\Users\alfre\OneDrive\Documentos\Agenda\agendas_medicas\static\historial_turnos.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. HIDE Footer on Screen
# We need to ensure that OUTSIDE the @media print block, the footer is hidden.
# We'll insert a style rule for #print-footer { display: none; } at the beginning of the <style> block or just before @media print.
# But actually, the safest way is if we have a general style block.
# Looking at the file, the <style> block starts around line 13.
# We'll just append it to the general CSS before @media print starts.

if '#print-footer { display: none; }' not in content:
    # Insert it before @media print
    content = content.replace('@media print {', '#print-footer { display: none; }\n        @media print {')

# 2. Fix Page Counter 0 Issue
# Removing 'counter-reset: page 0;' from everywhere.
content = content.replace('counter-reset: page 0;', '')
content = content.replace('counter-reset: page;', '') 
# We previously added 'counter-reset: page 0;' so removing that specific string works.

# 3. Ensure Print Visibility
# Verify if we have the block !important rule inside @media print.
# The previous script added/verified:
#             #print-footer {
#                 display: block !important;
#             }
# We keep that.

# 4. Cleanup
# Just to be clean, if there are double declarations or weird formatting from previous regexes, we leave them be as long as they are valid CSS.
# The critical fix is hidding it on screen and fixing the counter.

# 5. Fix Page Number "0"
# If we remove counter-reset, browser defaults to 1.
# We also have `counter-increment: page;` in `@page`.
# This is usually correct.

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
