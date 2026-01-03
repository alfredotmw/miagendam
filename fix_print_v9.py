import re

file_path = r'c:\Users\alfre\OneDrive\Documentos\Agenda\agendas_medicas\static\historial_turnos.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# STRATEGY V9: FIXED POSITION + STANDARD MARGINS
# User complains footer is "too high" on last page (tfoot behavior).
# Solution: Move content out of TFOOT and back to position:fixed.
# CRITICAL: We utilize the fact that margins are now 1cm (STANDARD), so bottom:0 is safe.

# 1. EXTRACT CURRENT FOOTER CONTENT
# We want the content we carefully built in V8 (with official logos).
# It's inside <tfoot>...<td> (CONTENT) </td>...</tfoot>

tfoot_pattern = r'<tfoot>\s*<tr>\s*<td>(.*?)</td>\s*</tr>\s*</tfoot>'
match = re.search(tfoot_pattern, content, re.DOTALL)

if match:
    footer_inner_content = match.group(1).strip()
    
    # 2. RESTORE TFOOT TO SPACER
    # We leave an empty spacer in tfoot so content doesn't overwrite our fixed footer.
    spacer_html = """<tfoot>
            <tr>
                <td>
                    <!-- Space reservation to prevent content overlaps with fixed footer -->
                    <div class="footer-space">&nbsp;</div>
                </td>
            </tr>
        </tfoot>"""
    
    content = re.sub(tfoot_pattern, spacer_html, content, flags=re.DOTALL)
    print("Restored TFOOT spacer.")

    # 3. INJECT INTO FIXED DIV
    # We place this at the end of the body.
    
    # We need a wrapping div that applies the fixed positioning.
    # The inner content already has some styling, but we need the container.
    
    fixed_footer_html = f"""
    <!-- PRINT FOOTER FIXED (V9) -->
    <div id="print-footer" class="print-footer-content">
        <table style="width: 100%; border: 0; border-collapse: collapse;">
            <tr>
                <td style="text-align: center; vertical-align: bottom;">
                    {footer_inner_content}
                </td>
            </tr>
        </table>
    </div>
    """
    
    idx_end = content.find('</body>')
    content = content[:idx_end] + fixed_footer_html + '\n    ' + content[idx_end:]
    print("Injected fixed footer at bottom of body.")

else:
    print("Could not find current TFOOT content. Aborting to avoid losing logos.")
    # Fallback: If we can't find it (maybe regex failed?), we should use the known V8 content string.
    # But let's assume it works since we just wrote it.

# 4. UPDATE CSS FOR FIXED FOOTER
# Ensure .print-footer-content has proper fixed styling.
# We want it bottom: 0.

current_css_pattern = r'\.print-footer-content\s*\{[^}]*\}'
new_css = """
            .print-footer-content {
                position: fixed;
                bottom: 0;
                left: 0;
                width: 100%;
                /* Height auto to fit content, or fixed? */
                /* Let's use auto/fit-content but ensure it references bottom */
                background: white;
                border-top: 1px solid #ccc;
                display: block !important;
                padding: 0; 
                z-index: 999999;
            }
"""
# Note: we kept margin: 1cm in @page, so bottom: 0 is 1cm from edge. Perfect.

content = re.sub(current_css_pattern, new_css.strip(), content)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
