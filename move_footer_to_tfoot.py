import re

file_path = 'static/historial_turnos.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Extract Base64 Source
match = re.search(r'<img src="(data:image/jpeg;base64,[^"]+)"', content)
if not match:
    print("Could not find base64 image source.")
    exit(1)

base64_src = match.group(1)
print("Found base64 source.")

# 2. Prepare new tfoot content
new_tfoot_content = f"""<div class="footer-space" style="height: auto; display: flex; align-items: flex-end; justify-content: center;">
                        <img src="{base64_src}" alt="Footer" style="max-width: 95%; height: auto; display: block;">
                    </div>"""

# 3. Replace tfoot content
# Find the existing tfoot div to replace
tfoot_pattern = r'<div class="footer-space"[^>]*>[\s\S]*?<!-- Footer Content -->[\s\S]*?</div>'
if re.search(tfoot_pattern, content):
    content = re.sub(tfoot_pattern, new_tfoot_content, content)
    print("Replaced tfoot content.")
else:
    # If pattern doesn't match exactly due to previous edits, try a broader one or just the inner part
    print("Could not match tfoot pattern exactly. Trying alternative...")
    # Manual check of the file shows: <div class="footer-space"\n ... <!-- Footer Content -->\n </div>
    # My regex might be slightly off on whitespace.
    content = re.sub(r'<div class="footer-space"[\s\S]*?</div>', new_tfoot_content, content, count=1) 
    # Be careful not to replace other footer-spaces if any (there is only one per tfoot usually)

# 4. Remove the fixed footer block at the end
# Pattern for the last div we added
fixed_footer_pattern = r'<div class="print-footer-content">[\s\S]*?</body>'
if re.search(fixed_footer_pattern, content):
    content = re.sub(fixed_footer_pattern, '</body>', content)
    print("Removed fixed footer block.")

# 5. Fix Margins in CSS
# Change margin-bottom: 30mm back to 10mm or similar, as tfoot reserves space now.
content = content.replace('margin-bottom: 30mm;', 'margin-bottom: 10mm;')
content = content.replace('bottom: 5mm !important;', '') # Cleanup old CSS rules just in case

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Done.")
