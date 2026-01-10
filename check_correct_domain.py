
import requests
from auth.jwt import create_access_token

# 1. Generate Token
token = create_access_token(
    data={"sub": "admin", "role": "ADMIN"}, 
    expires_minutes=525600
)

# 2. Construct URL with CORRECT domain from screenshot
correct_domain = "https://miagendam.onrender.com"
url = f"{correct_domain}/radioterapia/feed?token={token}"

print(f"Testing URL: {url}")

try:
    # 3. Test it
    resp = requests.get(url, timeout=10)
    print(f"Status Code: {resp.status_code}")
    if resp.status_code == 200:
        print("✅ SUCCESS! The correct domain is miagendam.onrender.com")
        print("Use this link!")
    elif resp.status_code == 404:
        print("❌ 404 Not Found on miagendam.onrender.com too.")
    else:
        print(f"❌ Error {resp.status_code}: {resp.text}")

except Exception as e:
    print(f"❌ Connection failed: {e}")
