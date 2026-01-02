import os

file_path = r'c:\Users\alfre\OneDrive\Documentos\Agenda\agendas_medicas\static\historial_turnos.html'

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
inside_media_print = False
footer_fix_applied = False

for line in lines:
    stripped = line.strip()
    
    # Track context (simple state machine)
    if '@media print' in line:
        inside_media_print = True
    
    # REMOVE counter-reset
    if 'counter-reset: page' in line:
        print(f"Removing line: {line.strip()}")
        continue # Skip this line
        
    # FIX Footer Visibility
    # We want to ensure #print-footer is hidden by default in global styles
    # We'll look for the ID definition.
    if '#print-footer {' in line and 'display: none' not in line and not inside_media_print:
        # If we see a rule for #print-footer not in print media, we make sure it's display: none
        # But parsing CSS line by line is hard.
        pass

    new_lines.append(line)

# Now, we need to inject the global "hide footer" rule if it's missing
content = "".join(new_lines)

# Inject global hide if not present
if '#print-footer { display: none; }' not in content:
    # Try to insert it before @media print
    if '@media print' in content:
        content = content.replace('@media print', '#print-footer { display: none; }\n        @media print')
        print("Added global hide rule for footer.")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
