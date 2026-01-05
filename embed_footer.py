import base64
import os

# Paths
html_path = 'static/historial_turnos.html'
image_path = 'static/footer_print.jpg'

# Read image and convert to base64
with open(image_path, 'rb') as img_file:
    b64_string = base64.b64encode(img_file.read()).decode('utf-8')

data_uri = f"data:image/jpeg;base64,{b64_string}"

# Read HTML
with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Target string to replace (using the absolute URL version I last put in)
target_tag = '<img src="https://miagendam.onrender.com/static/footer_print.jpg" alt="Footer"'
replacement_tag = f'<img src="{data_uri}" alt="Footer"'

if target_tag in content:
    new_content = content.replace(target_tag, replacement_tag)
    # Also fix the CSS bottom: 5mm -> bottom: 0 to be safe
    new_content = new_content.replace('bottom: 5mm !important;', 'bottom: 0 !important;')
    
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Successfully embedded base64 image and updated CSS.")
else:
    print("Target tag not found. Please check the file content.")
