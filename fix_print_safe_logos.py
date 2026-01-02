import re

file_path = r'c:\Users\alfre\OneDrive\Documentos\Agenda\agendas_medicas\static\historial_turnos.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. FIX CSS - Ensure Footer is Safe
# We need to update the .print-footer-content CSS to be ultra-safe.
# We'll replace the existing .print-footer-content block in the @media print.

# Current bad block might look like:
#             .print-footer-content {
#                 ...
#                 padding: 0 1cm 15px 1cm; 
#                 ...
#             }

new_footer_css = """
            .print-footer-content {
                position: fixed;
                bottom: 0px; /* Attach to bottom */
                left: 0;
                width: 100%;
                height: 50px;
                background: white;
                border-top: 1px solid #ccc;
                
                /* Reset display for table child */
                display: block !important;
                
                padding: 10px 1cm; /* Safe padding */
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
"""

# We'll use a regex to find the .print-footer-content block inside @media print?
# It's easier to just replace the whole @media print block again if we are confident, or surgically replace the class.
# Let's surgically replace the class definition since we know it's unique.
# We search for `.print-footer-content {` and match until the closing brace.
# This assumes no nested braces inside (which is true for this class).

pattern = r'\.print-footer-content\s*\{(?:[^{}]*)\}'
content = re.sub(pattern, new_footer_css.strip(), content)

# 2. REPLACE FOOTER HTML WITH TABLE
# Flexbox gap might be failing. Tables are bulletproof in print.
# We will use the same logos but in a table structure.

new_footer_html = """
    <!-- PRINT FOOTER SAFE MODE (TABLE) -->
    <div id="print-footer" class="print-footer-content">
        <table style="width: 100%; text-align: center; border: 0; border-collapse: collapse;">
            <tr>
                <td style="text-align: center; vertical-align: middle; font-family: sans-serif; font-size: 9px; color: black;">
                    
                    <span style="display: inline-block; vertical-align: middle;">
                        <b>San Martín Nº 2473</b>
                        &nbsp;
                        <svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24" fill="#25D366" style="vertical-align: middle;"><path d="M12.031 6.172c-3.181 0-5.767 2.586-5.768 5.766-.001 1.298.38 2.27 1.019 3.287l-.711 2.598 2.664-.698c.6.358 1.407.574 2.296.574h.001c3.181 0 5.768-2.586 5.768-5.766s-2.586-5.761-5.769-5.761zm-4.474 8.68l-.835.223.322-1.171c-.322-.513-.497-1.112-.497-1.73.001-1.801 1.465-3.266 3.267-3.266 1.801 0 3.266 1.465 3.266 3.266 0 1.801-1.465 3.266-3.266 3.266-.757 0-1.455-.262-2.022-.693l-.835.223zm10.976-13.852h-13.066c-1.377 0-2.5.9-2.5 2.217v13.633c0 1.317 1.123 2.217 2.5 2.217h6.632c.545 0 .918.736.567 1.111l-3.376 3.6c-.637.683.056 1.917 1.259 1.917h8.984c1.377 0 2.5-.9 2.5-2.217v-20.261c0-1.317-1.123-2.217-2.5-2.217z" /></svg>
                        3794684336
                    </span>

                    <span style="display: inline-block; margin: 0 15px; color: #ccc;">|</span>

                    <span style="display: inline-block; vertical-align: middle;">
                        <b>Colombia Nº 1249</b>
                        &nbsp;
                        <svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24" fill="#25D366" style="vertical-align: middle;"><path d="M12.031 6.172c-3.181 0-5.767 2.586-5.768 5.766-.001 1.298.38 2.27 1.019 3.287l-.711 2.598 2.664-.698c.6.358 1.407.574 2.296.574h.001c3.181 0 5.768-2.586 5.768-5.766s-2.586-5.761-5.769-5.761zm-4.474 8.68l-.835.223.322-1.171c-.322-.513-.497-1.112-.497-1.73.001-1.801 1.465-3.266 3.267-3.266 1.801 0 3.266 1.465 3.266 3.266 0 1.801-1.465 3.266-3.266 3.266-.757 0-1.455-.262-2.022-.693l-.835.223zm10.976-13.852h-13.066c-1.377 0-2.5.9-2.5 2.217v13.633c0 1.317 1.123 2.217 2.5 2.217h6.632c.545 0 .918.736.567 1.111l-3.376 3.6c-.637.683.056 1.917 1.259 1.917h8.984c1.377 0 2.5-.9 2.5-2.217v-20.261c0-1.317-1.123-2.217-2.5-2.217z" /></svg>
                        3794409595
                    </span>
                    
                    <span style="display: inline-block; margin: 0 15px; color: #ccc;">|</span>
                    
                    <span style="display: inline-block; vertical-align: middle;">
                        Corrientes
                        &nbsp;
                        <svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24" fill="#E1306C" style="vertical-align: middle;"><path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z" /></svg>
                        @oncologicocorrientes
                    </span>

                </td>
            </tr>
        </table>
    </div>
"""

# Replace the existing footer div (whatever it is) with this new one
# We search for <div id="print-footer" ... </div> ... </div> ? 
# Or just search for the previous content we injected "San Martín"
start_marker = '<div id="print-footer"'
idx_start = content.find(start_marker)
if idx_start != -1:
    idx_end = content.find('</body>')
    # Replace content from footer start to body end
    content = content[:idx_start] + new_footer_html + '\n' + content[idx_end:]

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
