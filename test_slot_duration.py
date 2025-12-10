import requests
import sys
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"

# 1. Login
print("Logging in...")
r = requests.post(f"{BASE_URL}/users/login", json={"username": "Alfredo", "password": "1234"})
if r.status_code != 200:
    print(f"Login failed: {r.text}")
    sys.exit(1)
token = r.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# 2. Get agendas and find PET or CAMARA_GAMMA
print("Getting agendas...")
r = requests.get(f"{BASE_URL}/agendas/", headers=headers)
agendas = r.json()
target_agenda = None
for a in agendas:
    if a["tipo"] in ["PET", "CAMARA_GAMMA"]:
        target_agenda = a
        break

if not target_agenda:
    print("No PET or CAMARA_GAMMA agenda found")
    sys.exit(1)

print(f"Found agenda: {target_agenda['nombre']} ({target_agenda['tipo']})")

# 3. Get slots
print("Getting slots...")
today = datetime.now().strftime("%Y-%m-%d")
r = requests.get(f"{BASE_URL}/agendas/{target_agenda['id']}/slots?fecha={today}", headers=headers)
slots = r.json()

if not slots:
    print("No slots found")
    sys.exit(1)

# 4. Check duration
# We can infer duration by looking at the difference between first and second slot
if len(slots) < 2:
    print("Not enough slots to determine duration")
    sys.exit(1)

t1 = datetime.strptime(slots[0]["hora"], "%H:%M")
t2 = datetime.strptime(slots[1]["hora"], "%H:%M")
diff = (t2 - t1).total_seconds() / 60

print(f"Slot 1: {slots[0]['hora']}")
print(f"Slot 2: {slots[1]['hora']}")
print(f"Difference: {diff} minutes")

if diff == 60:
    print("SUCCESS: Duration is 60 minutes")
else:
    print(f"FAILURE: Duration is {diff} minutes")
