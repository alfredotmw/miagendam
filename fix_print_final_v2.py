import re

file_path = r'c:\Users\alfre\OneDrive\Documentos\Agenda\agendas_medicas\static\historial_turnos.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# We need to modify the @media print block.
# We will use the same "replace block" strategy.

start_marker = '@media print {'
start_idx = content.find(start_marker)

# NEW REVISED CSS
# 1. @page margin: 0 (Hides browser headers) -> KEEP
# 2. html, body height: 100% -> REMOVE (Fixes page counter/pagination)
# 3. Footer positioning -> ADJUST for zero margin context.
#    Since the page has 0 margin, the footer at bottom: 0 is at the physical edge.
#    Most printers have a non-printable area of ~5mm.
#    So we should put the footer at bottom: 0 but with padding-bottom: 10mm inside it?
#    Or better: position fixed bottom 0, height 20mm, padding-bottom 5mm.

new_css_block = """@media print {
            /* 1. HIDE BROWSER HEADERS/FOOTERS */
            @page {
                size: A4;
                margin: 0; 
            }

            /* 2. BODY SETUP - REMOVED HEIGHT: 100% TO FIX PAGINATION */
            html, body {
                margin: 0 !important;
                padding: 0 !important;
                background: white !important;
                /* height: 100%;  <-- REMOVED THIS */
            }

            /* 3. BASIC VISIBILITY */
            body > * { display: none !important; }
            #print-layout { display: table !important; }
            #print-footer { display: flex !important; }

            .sidebar, .logout-btn, .search-header-container, #welcome-state, .modal, .filters-card { 
                display: none !important; 
            }

            /* 4. LAYOUT STRUCTURE */
            #print-layout {
                width: 100%;
                border-collapse: collapse;
            }
            #print-layout thead { display: table-header-group; }
            #print-layout tfoot { display: table-footer-group; }
            #print-layout tbody { display: table-row-group; }

            /* 5. SPACERS */
            /* We need to push content away from easy cut-off zones since we have 0 margins */
            .header-space { 
                height: 120px; 
            }
            .footer-space { 
                height: 80px; 
            }

            /* 6. FIXED HEADER */
            .print-header-content {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100px;
                background: white;
                padding: 10px 1cm; 
                box-sizing: border-box;
                border-bottom: 2px solid #eee;
                z-index: 1000;
            }

            /* 7. FIXED FOOTER */
            .print-footer-content {
                position: fixed;
                bottom: 0;
                left: 0;
                width: 100%;
                height: 60px;
                background: white;
                border-top: 1px solid #ccc;
                
                display: flex !important;
                align-items: center;
                justify-content: center;
                text-align: center;
                
                /* CRITICAL: Add padding to lift text above physical printer margin */
                padding: 0 1cm 15px 1cm; 
                box-sizing: border-box;
                z-index: 99999;
            }
            
            /* 8. PAGE NUMBER */
            .print-footer-content::after {
                content: counter(page);
                position: absolute;
                top: 15px; 
                right: 30px;
                font-size: 10px;
                font-weight: bold;
                color: #000;
            }

            /* 9. CONTENT STYLES */
            .content-container {
                padding: 0 1cm; /* Manual margins since @page is 0 */
            }
            .patient-card {
                border: 1px solid #ddd;
                padding: 15px;
                margin-bottom: 20px;
                box-shadow: none !important;
                page-break-inside: avoid;
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
    # Find matching closing brace
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
        content = content[:start_idx] + new_css_block + content[end_idx:]
        print("Updated print block: Removed height:100% (fix page 0) but kept margin:0 (hide headers).")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
