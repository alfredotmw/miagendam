
from main import app

print("Checking registered routes in main.app:")
found = False
for route in app.routes:
    if hasattr(route, 'path'):
        print(f" - {route.path} [{route.name}]")
        if "/radioterapia/feed" in route.path:
            found = True

if found:
    print("\n✅ The route /radioterapia/feed IS registered locally.")
else:
    print("\n❌ The route /radioterapia/feed is NOT registered locally.")
