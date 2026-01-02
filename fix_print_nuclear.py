import re

file_path = r'c:\Users\alfre\OneDrive\Documentos\Agenda\agendas_medicas\static\historial_turnos.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. REMOVE EXISTING FOOTER(s)
# We will match widely to kill any variation of known footer ids
# The ID is print-footer
footer_regex = r'<div id="print-footer".*?</div>\s*</div>' # Match the nested structure we saw in previous reads
content = re.sub(footer_regex, '', content, flags=re.DOTALL)

# Also try simplified one just in case
content = re.sub(r'<div id="print-footer".*?</div>', '', content, flags=re.DOTALL)

# 2. REMOVE EXISTING @MEDIA PRINT
# It starts around line 102
# We will use regex to find "@media print {" and match until the logical end of it.
# This is hard with regex due to nested braces.
# Instead, we will construct a "clean" file by identifying the block visually from the file read start/end lines
# From previous `view_file`, we know:
# @media print { is at line 102
# The closing brace for it is at line 236 approximately.
# Let's find the start index
start_marker = '@media print {'
start_idx = content.find(start_marker)

if start_idx != -1:
    # We will walk forward to find the matching brace
    brace_count = 0
    end_idx = -1
    for i in range(start_idx, len(content)):
        if content[i] == '{':
            brace_count += 1
        elif content[i] == '}':
            brace_count -= 1
            if brace_count == 0:
                end_idx = i + 1
                break
    
    if end_idx != -1:
        # Remove the block
        print(f"Removing media print block from {start_idx} to {end_idx}")
        content = content[:start_idx] + content[end_idx:]
    else:
        print("Could not find closing brace for @media print")

# 3. REMOVE STRAY CSS
# Remove the #print-footer { display: none; } we added
content = content.replace('#print-footer { display: none; }', '')

# 4. INJECT NEW CLEAN CSS
# We will inject it before </head>
new_css = """
    <style>
        /* GLOBAL HIDE FOOTER ON SCREEN */
        #print-footer { display: none; }

        @media print {
            /* GLOBAL PAGE RESET */
            html, body {
                margin: 0 !important;
                padding: 0 !important;
                background: white !important;
                height: 100%;
                /* CRITICAL: Do NOT use counter-reset: page here unless you know what you are doing. */
            }

            @page {
                size: A4;
                margin: 10mm; /* Standard margin */
                counter-increment: page; /* Ensure counter increments */
            }

            /* HIDE UI ELEMENTS */
            body > * { display: none !important; }
            
            /* SHOW PRINT LAYOUT */
            #print-layout { display: table !important; width: 100%; }
            #print-footer { display: block !important; }

            /* LAYOUT VISIBILITY */
            .sidebar, .logout-btn, .search-header-container, #welcome-state, .modal, .filters-card { display: none !important; }

            /* TABLE LAYOUT */
            #print-layout { width: 100%; border-collapse: collapse; }
            #print-layout thead { display: table-header-group; }
            #print-layout tfoot { display: table-footer-group; }
            #print-layout tbody { display: table-row-group; }

            /* SPACERS */
            .header-space { height: 100px; }
            .footer-space { height: 50px; }

            /* FIXED HEADER */
            .print-header-content {
                position: fixed; top: 0; left: 0; width: 100%; height: 100px;
                background: white; border-bottom: 2px solid #eee;
                padding: 10px; box-sizing: border-box;
            }

            /* FIXED FOOTER - THE CRITICAL PART */
            .print-footer-content {
                position: fixed;
                bottom: 0;
                left: 0;
                width: 100%;
                height: 50px;
                background: white;
                border-top: 1px solid #ccc;
                text-align: center;
                /* Flexbox for centering text */
                display: flex !important; 
                align-items: center; 
                justify-content: center;
                z-index: 99999;
                padding: 5px;
                box-sizing: border-box;
            }
            
            /* PAGE NUMBER */
            .print-footer-content::after {
                content: counter(page);
                position: absolute;
                right: 20px;
                top: 15px;
                font-size: 12px;
                font-weight: bold;
                color: #000;
            }
            
            /* CONTENT STYLING */
            .content-container { padding: 20px 0; }
            .patient-card { border: 1px solid #ddd; padding: 10px; margin-bottom: 20px; box-shadow: none; }
            .timeline-card { border: 1px solid #ddd; margin-bottom: 10px; page-break-inside: avoid; }
        }
    </style>
"""

# Insert new CSS before closing head
content = content.replace('</head>', new_css + '\n</head>')

# 5. INJECT NEW FOOTER HTML
# Insert before closing body
# We must ensure it's outside the table
new_footer_html = """
    <!-- PRINT FOOTER -->
    <div id="print-footer" class="print-footer-content">
        <p style="margin: 0; padding: 0; font-size: 10px; color: black; font-family: sans-serif;">
            San Martín Nº 2473 - whatsapp 3794684336 y Colombia Nº 1249 - whatsapp 3794409595. Corrientes. Instagram @oncologicocorrientes
        </p>
    </div>
"""
content = content.replace('</body>', new_footer_html + '\n</body>')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
