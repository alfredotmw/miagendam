import re
import os

file_path = r'c:\Users\alfre\OneDrive\Documentos\Agenda\agendas_medicas\static\historial_turnos.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Fix CSS counter-increment
# Find:
#             @page {
#                 margin: 0;
#                 size: auto;
#             }
# Replace with version adding counter-increment: page;

css_pattern = r'(@page\s*{\s*margin:\s*0;\s*size:\s*auto;\s*})'
css_replacement = r'''@page {
                margin: 0;
                size: auto;
                counter-increment: page;
            }'''

# using simple string replace if regex fails due to whitespace specifics, but trying regex first to be safe
# specifically matching the exact block created in previous step
css_search_str = """            @page {
                margin: 0;
                size: auto;
            }"""

if css_search_str in content:
    content = content.replace(css_search_str, css_replacement)
    print("CSS fixed successfully.")
else:
    print("CSS block not found via exact match, trying regex...")
    content = re.sub(css_pattern, css_replacement, content)


# 2. Replace Footer HTML
# Target: <div id="print-footer" ... </table> ... </div>
# New content: Flexbox divs

new_footer_html = """    <!-- Footer moved OUT of the table for reliable fixed positioning -->
    <div id="print-footer" class="print-footer-content" style="display: none;">
        <div style="display: flex; justify-content: space-between; align-items: center; height: 100%; width: 100%;">
            <!-- Address 1 -->
            <div style="flex: 1; text-align: center;">
                <div style="display: flex; flex-direction: column; align-items: center; gap: 2px;">
                    <strong>San Martín Nº 2473</strong>
                    <div style="display: flex; align-items: center; gap: 4px; justify-content: center;">
                        <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="#25D366">
                            <path d="M12.031 6.172c-3.181 0-5.767 2.586-5.768 5.766-.001 1.298.38 2.27 1.019 3.287l-.711 2.598 2.664-.698c.6.358 1.407.574 2.296.574h.001c3.181 0 5.768-2.586 5.768-5.766s-2.586-5.761-5.769-5.761zm-4.474 8.68l-.835.223.322-1.171c-.322-.513-.497-1.112-.497-1.73.001-1.801 1.465-3.266 3.267-3.266 1.801 0 3.266 1.465 3.266 3.266 0 1.801-1.465 3.266-3.266 3.266-.757 0-1.455-.262-2.022-.693l-.835.223zm10.976-13.852h-13.066c-1.377 0-2.5.9-2.5 2.217v13.633c0 1.317 1.123 2.217 2.5 2.217h6.632c.545 0 .918.736.567 1.111l-3.376 3.6c-.637.683.056 1.917 1.259 1.917h8.984c1.377 0 2.5-.9 2.5-2.217v-20.261c0-1.317-1.123-2.217-2.5-2.217z" fill-opacity="0" />
                            <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297a11.815 11.815 0 00-8.412-3.488c-6.529 0-11.843 5.314-11.849 11.847a11.812 11.812 0 001.812 6.313l-1.936 7.07 7.243-1.902a11.751 11.751 0 006.355 1.303h.004c6.531 0 11.844-5.316 11.849-11.849.006-3.167-1.229-6.142-3.475-8.385" fill="#25D366" />
                        </svg>
                        <span>3794684336</span>
                    </div>
                </div>
            </div>

            <!-- Address 2 -->
            <div style="flex: 1; text-align: center; border-left: 1px solid #ddd; border-right: 1px solid #ddd;">
                <div style="display: flex; flex-direction: column; align-items: center; gap: 2px;">
                    <strong>Colombia Nº 1249</strong>
                    <div style="display: flex; align-items: center; gap: 4px; justify-content: center;">
                        <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="#25D366">
                            <path d="M12.031 6.172c-3.181 0-5.767 2.586-5.768 5.766-.001 1.298.38 2.27 1.019 3.287l-.711 2.598 2.664-.698c.6.358 1.407.574 2.296.574h.001c3.181 0 5.768-2.586 5.768-5.766s-2.586-5.761-5.769-5.761zm-4.474 8.68l-.835.223.322-1.171c-.322-.513-.497-1.112-.497-1.73.001-1.801 1.465-3.266 3.267-3.266 1.801 0 3.266 1.465 3.266 3.266 0 1.801-1.465 3.266-3.266 3.266-.757 0-1.455-.262-2.022-.693l-.835.223zm10.976-13.852h-13.066c-1.377 0-2.5.9-2.5 2.217v13.633c0 1.317 1.123 2.217 2.5 2.217h6.632c.545 0 .918.736.567 1.111l-3.376 3.6c-.637.683.056 1.917 1.259 1.917h8.984c1.377 0 2.5-.9 2.5-2.217v-20.261c0-1.317-1.123-2.217-2.5-2.217z" fill-opacity="0" />
                            <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297a11.815 11.815 0 00-8.412-3.488c-6.529 0-11.843 5.314-11.849 11.847a11.812 11.812 0 001.812 6.313l-1.936 7.07 7.243-1.902a11.751 11.751 0 006.355 1.303h.004c6.531 0 11.844-5.316 11.849-11.849.006-3.167-1.229-6.142-3.475-8.385" fill="#25D366" />
                        </svg>
                        <span>3794409595</span>
                    </div>
                </div>
            </div>

            <!-- Social Media -->
            <div style="flex: 1; text-align: center;">
                 <div style="display: flex; align-items: center; gap: 4px; justify-content: center;">
                    <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="#E1306C">
                        <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z" />
                    </svg>
                    <span>@oncologicocorrientes</span>
                </div>
            </div>
        </div>
    </div>"""

# Robust regex to find the footer block.
# We search for <div id="print-footer" ... then match non-greedily until we see </table> stuck to a </div> or similar structure.
# But since we look for "</table>" and "</div>", and we know the previous content implies a table closure.
# Let's search for the ID start... and the known end.
# Actually, since we have the full file content in memory, and we know the strings *probably*, we could try string replace for the header part too?
# But `re.sub` is safer for whitespace variance.

footer_regex = r'(<div id="print-footer"[^>]*>.*?</table>\s*</div>)'

if re.search(footer_regex, content, re.DOTALL):
    content = re.sub(footer_regex, new_footer_html, content, flags=re.DOTALL)
    print("Footer replaced successfully via regex.")
else:
    print("Footer block not found via regex.")
    # Fallback debug: print context around "print-footer"
    start = content.find('id="print-footer"')
    if start != -1:
        print(f"DEBUG: Found footer start at {start}. Context: {content[start:start+200]}...")
    else:
        print("DEBUG: Footer start NOT found.")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
