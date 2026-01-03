import re

file_path = r'c:\Users\alfre\OneDrive\Documentos\Agenda\agendas_medicas\static\historial_turnos.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# STRATEGY V7: EMBED CONTENT DIRECTLY INTO TFOOT
# User reports "no line comes out". Fixed positioning is proving flaky on their system context.
# We will put the content INSIDE the <tfoot ... > <tr><td> ... </td></tr> </tfoot>
# This guarantees it sits at the bottom of the table flow on every page.

# 1. Define the footer content HTML (Same as V6 but safe for embedding)
footer_inner_html = """
                    <div style="text-align: center; font-family: sans-serif; font-size: 9px; color: #333; padding: 10px 0; border-top: 1px solid #ccc;">
                        
                        <!-- Line 1: Addresses and City -->
                        <div style="margin-bottom: 5px; font-weight: bold;">
                            San Martín Nº 2473 &nbsp;|&nbsp; Colombia Nº 1249 &nbsp;|&nbsp; Corrientes, Capital
                        </div>

                        <!-- Line 2: Contact with SVGs -->
                        <div style="display: flex; justify-content: center; align-items: center; gap: 15px;">
                            
                            <!-- WhatsApp 1 -->
                            <span style="display: inline-flex; align-items: center; gap: 3px;">
                                <svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24" fill="#25D366"><path d="M12.031 6.172c-3.181 0-5.767 2.586-5.768 5.766-.001 1.298.38 2.27 1.019 3.287l-.711 2.598 2.664-.698c.6.358 1.407.574 2.296.574h.001c3.181 0 5.768-2.586 5.768-5.766s-2.586-5.761-5.769-5.761zm-4.474 8.68l-.835.223.322-1.171c-.322-.513-.497-1.112-.497-1.73.001-1.801 1.465-3.266 3.267-3.266 1.801 0 3.266 1.465 3.266 3.266 0 1.801-1.465 3.266-3.266 3.266-.757 0-1.455-.262-2.022-.693l-.835.223zm10.976-13.852h-13.066c-1.377 0-2.5.9-2.5 2.217v13.633c0 1.317 1.123 2.217 2.5 2.217h6.632c.545 0 .918.736.567 1.111l-3.376 3.6c-.637.683.056 1.917 1.259 1.917h8.984c1.377 0 2.5-.9 2.5-2.217v-20.261c0-1.317-1.123-2.217-2.5-2.217z" /></svg>
                                3794-684336
                            </span>

                            <!-- WhatsApp 2 -->
                            <span style="display: inline-flex; align-items: center; gap: 3px;">
                                <svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24" fill="#25D366"><path d="M12.031 6.172c-3.181 0-5.767 2.586-5.768 5.766-.001 1.298.38 2.27 1.019 3.287l-.711 2.598 2.664-.698c.6.358 1.407.574 2.296.574h.001c3.181 0 5.768-2.586 5.768-5.766s-2.586-5.761-5.769-5.761zm-4.474 8.68l-.835.223.322-1.171c-.322-.513-.497-1.112-.497-1.73.001-1.801 1.465-3.266 3.267-3.266 1.801 0 3.266 1.465 3.266 3.266 0 1.801-1.465 3.266-3.266 3.266-.757 0-1.455-.262-2.022-.693l-.835.223zm10.976-13.852h-13.066c-1.377 0-2.5.9-2.5 2.217v13.633c0 1.317 1.123 2.217 2.5 2.217h6.632c.545 0 .918.736.567 1.111l-3.376 3.6c-.637.683.056 1.917 1.259 1.917h8.984c1.377 0 2.5-.9 2.5-2.217v-20.261c0-1.317-1.123-2.217-2.5-2.217z" /></svg>
                                3794-409595
                            </span>

                            <!-- Instagram -->
                            <span style="display: inline-flex; align-items: center; gap: 3px;">
                                <svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24" fill="#E1306C"><path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z" /></svg>
                                @oncologicocorrientes
                            </span>
                        </div>
                    </div>
"""

# 2. LOCATE TFOOT AND INJECT
# Look for <tfoot> ... <td> ... </td> ... </tfoot>
# Current:
#         <tfoot>
#             <tr>
#                 <td>
#                     <!-- Space reservation to prevent content overlaps with fixed footer -->
#                     <div class="footer-space">&nbsp;</div>
#                 </td>
#             </tr>
#         </tfoot>

tfoot_pattern = r'<tfoot>\s*<tr>\s*<td>(.*?)</td>\s*</tr>\s*</tfoot>'
replacement = f"""<tfoot>
            <tr>
                <td>
                    {footer_inner_html}
                </td>
            </tr>
        </tfoot>"""

# We use re.DOTALL to match across newlines
if re.search(tfoot_pattern, content, re.DOTALL):
    content = re.sub(tfoot_pattern, replacement, content, flags=re.DOTALL)
    print("Injected footer content into TFOOT.")
else:
    print("Could not find TFOOT block to replace.")

# 3. CLEAN UP OLD FIXED FOOTER
# Remove the <div id="print-footer" ... </div> block at the end
clean_pattern = r'<div id="print-footer".*?</div>\s*</body>'
# Note: The div is quite long now, regex needs to be robust. 
# Or we can just truncate.
start_marker = '<div id="print-footer"'
idx_start = content.find(start_marker)
if idx_start != -1:
    idx_end = content.find('</body>')
    # Remove it
    content = content[:idx_start] + '\n    ' + content[idx_end:]
    print("Removed old ID=print-footer div.")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
