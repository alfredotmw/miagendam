from auth.jwt import create_access_token
from datetime import timedelta

def generate_link():
    # Create a token valid for 365 days (525600 minutes)
    token = create_access_token(
        data={"sub": "admin", "role": "ADMIN"}, 
        expires_minutes=525600
    )
    # Print the Excel Data Feed Link
    link = f"https://miagendam.onrender.com/analytics/excel_feed?token={token}"
    with open("link_final.txt", "w") as f:
        f.write(link)
    print("Link written to link_final.txt")

if __name__ == "__main__":
    generate_link()
