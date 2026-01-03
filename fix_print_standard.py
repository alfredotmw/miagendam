import re

file_path = r'c:\Users\alfre\OneDrive\Documentos\Agenda\agendas_medicas\static\historial_turnos.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# We need to replace the @media print block with a STANDARD, SAFE version.
# No more tricks. Standard A4 margins. Sidebar hidden. Table layout.

# Find the start of @media print
start_marker = '@media print {'
start_idx = content.find(start_marker)

new_css_block = """@media print {
            /* 1. RESTORE STANDARD MARGINS - This brings back browser headers but ensures content prints */
            @page {
                size: A4;
                margin: 1cm; 
                counter-increment: page;
            }

            /* 2. BODY SETUP */
            html, body {
                margin: 0 !important;
                padding: 0 !important;
                background: white !important;
            }

            /* 3. BASIC VISIBILITY */
            body > * { display: none !important; }
            #print-layout { display: table !important; }
            /* Footer is shown, but we don't need fixed positioning hacks anymore? 
               Actually, for a repeating footer on every page, Fixed is best. 
               But with standard margins, bottom: 0 is RELATIVE to the margin edge, which is SAFE. */
            #print-footer { display: block !important; }

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
            .header-space { height: 100px; }
            .footer-space { height: 60px; }

            /* 6. FIXED HEADER */
            .print-header-content {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 90px;
                background: white;
                border-bottom: 2px solid #eee;
                z-index: 1000;
                /* No excess padding needed if we have page margins */
                box-sizing: border-box;
            }

            /* 7. FIXED FOOTER */
            .print-footer-content {
                position: fixed;
                bottom: 0;
                left: 0;
                width: 100%;
                height: 50px;
                background: white;
                border-top: 1px solid #ccc;
                
                display: block !important;
                
                /* Standard padding */
                padding: 5px 0; 
                box-sizing: border-box;
                z-index: 999999;
            }
            
            /* Ensure SVGs print correctly */
            .print-footer-content svg {
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
                display: inline-block;
                vertical-align: middle;
            }
            
            /* 8. PAGE NUMBER */
            .print-footer-content::after {
                content: counter(page);
                position: absolute;
                top: 15px; 
                right: 0; /* Align to right margin */
                font-size: 10px;
                font-weight: bold;
                color: #000;
            }

            /* 9. CONTENT STYLES */
            .content-container {
                padding: 10px 0;
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
        print("Restored standard margins to ensure footer printability.")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
