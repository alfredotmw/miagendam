import re

file_path = r'c:\Users\alfre\OneDrive\Documentos\Agenda\agendas_medicas\static\historial_turnos.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Target the existing footer div to replace it
# We know it looks like <div id="print-footer" ... > ... </div>
# We'll use regex to grab the block.

footer_regex = r'<div id="print-footer".*?</div>\s*</div>' # Trying to match nested div structure if any
# Actually, the last version was simpler:
#     <div id="print-footer" class="print-footer-content">
#         <p ...> ... </p>
#     </div>

# Let's match from <div id="print-footer" to the closing </div> of the outer div.
# Since we know the content is specific, we can try to matches that too.

new_footer_html = """    <!-- PRINT FOOTER WITH LOGOS -->
    <div id="print-footer" class="print-footer-content">
        <div style="display: flex; justify-content: center; align-items: center; gap: 15px; width: 100%; font-family: sans-serif; font-size: 9px; color: black;">
            
            <!-- Address 1 -->
            <div style="display: flex; align-items: center; gap: 4px;">
                <strong>San Martín Nº 2473</strong>
                <svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24" fill="#25D366" style="margin-top: 1px;"><path d="M12.031 6.172c-3.181 0-5.767 2.586-5.768 5.766-.001 1.298.38 2.27 1.019 3.287l-.711 2.598 2.664-.698c.6.358 1.407.574 2.296.574h.001c3.181 0 5.768-2.586 5.768-5.766s-2.586-5.761-5.769-5.761zm-4.474 8.68l-.835.223.322-1.171c-.322-.513-.497-1.112-.497-1.73.001-1.801 1.465-3.266 3.267-3.266 1.801 0 3.266 1.465 3.266 3.266 0 1.801-1.465 3.266-3.266 3.266-.757 0-1.455-.262-2.022-.693l-.835.223zm10.976-13.852h-13.066c-1.377 0-2.5.9-2.5 2.217v13.633c0 1.317 1.123 2.217 2.5 2.217h6.632c.545 0 .918.736.567 1.111l-3.376 3.6c-.637.683.056 1.917 1.259 1.917h8.984c1.377 0 2.5-.9 2.5-2.217v-20.261c0-1.317-1.123-2.217-2.5-2.217z" /></svg>
                <span>3794684336</span>
            </div>

            <span style="color: #ccc;">|</span>

            <!-- Address 2 -->
            <div style="display: flex; align-items: center; gap: 4px;">
                <strong>Colombia Nº 1249</strong>
                <svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24" fill="#25D366" style="margin-top: 1px;"><path d="M12.031 6.172c-3.181 0-5.767 2.586-5.768 5.766-.001 1.298.38 2.27 1.019 3.287l-.711 2.598 2.664-.698c.6.358 1.407.574 2.296.574h.001c3.181 0 5.768-2.586 5.768-5.766s-2.586-5.761-5.769-5.761zm-4.474 8.68l-.835.223.322-1.171c-.322-.513-.497-1.112-.497-1.73.001-1.801 1.465-3.266 3.267-3.266 1.801 0 3.266 1.465 3.266 3.266 0 1.801-1.465 3.266-3.266 3.266-.757 0-1.455-.262-2.022-.693l-.835.223zm10.976-13.852h-13.066c-1.377 0-2.5.9-2.5 2.217v13.633c0 1.317 1.123 2.217 2.5 2.217h6.632c.545 0 .918.736.567 1.111l-3.376 3.6c-.637.683.056 1.917 1.259 1.917h8.984c1.377 0 2.5-.9 2.5-2.217v-20.261c0-1.317-1.123-2.217-2.5-2.217z" /></svg>
                <span>3794409595</span>
            </div>

            <span style="color: #ccc;">|</span>

            <!-- Instagram -->
            <div style="display: flex; align-items: center; gap: 4px;">
                <span>Corrientes</span>
                <svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24" fill="#E1306C" style="margin-top: 1px;"><path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z" /></svg>
                <span>@oncologicocorrientes</span>
            </div>

        </div>
    </div>"""

# Remove old footer (regex)
content = re.sub(r'<div id="print-footer".*?</div>', '', content, flags=re.DOTALL)
# The regex above is slightly risky if nested divs exist in the simplified version, but the simplified version was:
# <div id="print-footer" class="print-footer-content">
#   <p ...> ... </p>
# </div>
# So it matches until the FIRST </div>? No, lazy match `.*?` matches until the FIRST `</div>`.
# The nested <p> doesn't have a div. But wait, if I used a nested div structure before...
# Let's use a robust replace by finding specific string if possible.
# The previous footer had "San Martín Nº 2473" in text.

if "San Martín Nº 2473" in content:
    # Safe to assume we can find the block start and end?
    # Actually, simpler is just to replace the specific known previous block if possible.
    # But regex `re.sub(r'<div id="print-footer".*?</div>\s*</div>', ...)` handles nested div if we match 2 divs?
    # Let's match strictly the ID and remove until the </body> since it's the last thing.
    
    idx = content.find('<div id="print-footer"')
    if idx != -1:
        # Cut everything from there to </body>
        body_end = content.find('</body>')
        content = content[:idx] + new_footer_html + '\n\n' + content[body_end:]
    else:
        print("Could not find footer div to replace.")
        # Inject before body end
        content = content.replace('</body>', new_footer_html + '\n</body>')
else:
    # If not found, inject
    content = content.replace('</body>', new_footer_html + '\n</body>')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
