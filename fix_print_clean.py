import re

file_path = r'c:\Users\alfre\OneDrive\Documentos\Agenda\agendas_medicas\static\historial_turnos.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# We need to replace the @media print CSS block we just added (or whatever is there) with the "Clean Margin" version.
# We'll use the same technique: find @media print and replace it.

start_marker = '@media print {'
start_idx = content.find(start_marker)

# Construct the NEW CSS with margin: 0
new_css_block = """@media print {
            /* 1. REMOVE BROWSER HEADERS/FOOTERS by setting margin to 0 */
            @page {
                size: A4;
                margin: 0; 
                padding: 0;
            }

            /* 2. BODY SETUP */
            html, body {
                margin: 0 !important;
                padding: 0 !important;
                background: white !important;
                width: 100%;
                height: 100%;
            }

            /* 3. HIDE NON-PRINT ELEMENTS */
            body > * { display: none !important; }
            #print-layout { display: table !important; }
            #print-footer { display: flex !important; } /* Use flex for the footer div */
            
            .sidebar, .logout-btn, .search-header-container, #welcome-state, .modal, .filters-card { 
                display: none !important; 
            }

            /* 4. LAYOUT STRUCTURE (Table method for paging) */
            #print-layout {
                width: 100%;
                border-collapse: collapse;
            }
            #print-layout thead { display: table-header-group; }
            #print-layout tfoot { display: table-footer-group; }
            #print-layout tbody { display: table-row-group; }

            /* 5. SPACERS (Reserve space for fixed header/footer) */
            /* These empty divs in the table push the body content away from the edges */
            .header-space { 
                height: 120px; /* Space for logo + margins */
            }
            .footer-space { 
                height: 80px; /* Space for footer + margins */
            }

            /* 6. FIXED HEADER */
            .print-header-content {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100px;
                background: white;
                /* Padding simulates the margin */
                padding: 10px 1cm; 
                box-sizing: border-box;
                border-bottom: 2px solid #eee;
                z-index: 1000;
            }

            /* 7. FIXED FOOTER (The one the user wants) */
            .print-footer-content {
                position: fixed;
                bottom: 0;
                left: 0;
                width: 100%;
                height: 60px; /* Fixed height */
                background: white;
                border-top: 1px solid #ccc;
                
                /* Centering */
                display: flex !important;
                align-items: center;
                justify-content: center;
                text-align: center;
                
                /* Margins/Padding inside the 0-margin page */
                padding: 0 1cm 10px 1cm; /* Bottom padding gives it some lift from paper edge */
                box-sizing: border-box;
                z-index: 99999;
            }
            
            /* 8. PAGE NUMBER */
            /* We'll put it in the footer container's after pseudo-element */
            /* Since margin is 0, we position relative to the window/paper */
            .print-footer-content::after {
                content: counter(page);
                position: absolute;
                top: 10px;    /* Distancia desde el borde superior del footer */
                right: 30px;  /* Distancia derecha */
                font-size: 10px;
                font-weight: bold;
                color: #000;
            }

            /* 9. CONTENT STYLES */
            .content-container {
                padding: 0 1cm; /* Side margins for the text content */
            }
            .patient-card {
                border: 1px solid #ddd;
                padding: 15px;
                margin-bottom: 20px;
                box-shadow: none !important;
            }
            .timeline-card {
                border: 1px solid #ddd;
                box-shadow: none !important;
                page-break-inside: avoid;
                margin-bottom: 10px;
            }
            .type-plan {
                background-color: #667eea !important;
                color: white !important;
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
            }
        }"""

if start_idx != -1:
    # Find matching closing brace for the existing block
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
        # replace
        content = content[:start_idx] + new_css_block + content[end_idx:]
        print("Replaced @media print block with Clean Margin version.")
    else:
        print("Could not find closing brace, appending new css anyway.")
        content = content.replace('</head>', '<style>' + new_css_block + '</style>\n</head>')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
