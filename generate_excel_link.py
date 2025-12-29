from auth.jwt import create_access_token
from datetime import timedelta

def generate_link():
    # Generate for 'admin' (or generic access)
    # Long expiry: 365 days
    expires = 60 * 24 * 365 
    access_token = create_access_token(
        data={"sub": "admin", "role": "ADMIN"}, 
        expires_minutes=expires
    )
    
    # Base URL (Assuming Render URL or defaulting to localhost for dev)
    # Ideally should be the production URL. User asks for the link "here".
    # I will provide the relative part and ask them to append to domain, 
    # OR if I know the domain. I don't know the full Render domain strictly, 
    # but I can give the pattern.
    
    print(f"\n--- EXCEL LINK ---\n")
    print(f"/radioterapia/feed?token={access_token}")
    print(f"\n------------------\n")
    
    with open("token.txt", "w") as f:
        f.write(access_token)

if __name__ == "__main__":
    generate_link()
