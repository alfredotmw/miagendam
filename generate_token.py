from auth.jwt import create_access_token
from datetime import timedelta

def generate_link():
    # Create a token valid for 365 days (525600 minutes)
    token = create_access_token(
        data={"sub": "admin", "role": "ADMIN"}, 
        expires_minutes=525600
    )
    print(f"https://miagendam.onrender.com/radioterapia/feed?token={token}")

if __name__ == "__main__":
    generate_link()
