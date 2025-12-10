from sqlalchemy.orm import Session
from database import SessionLocal
from models.user import User
import bcrypt

def reset_password():
    db = SessionLocal()
    user = db.query(User).filter_by(username="Alfredo").first()
    if user:
        print(f"Found user {user.username}. Resetting password...")
        hashed_password = bcrypt.hashpw("1234".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        user.password = hashed_password
        db.commit()
        print("Password reset to '1234'.")
    else:
        print("User 'Alfredo' not found. Creating...")
        hashed_password = bcrypt.hashpw("1234".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        # Assuming UserRole is needed, but for simplicity let's try to import it or just omit if default
        from models.user import UserRole
        user = User(username="Alfredo", password=hashed_password, role=UserRole.ADMIN)
        db.add(user)
        db.commit()
        print("User 'Alfredo' created with password '1234'.")
    db.close()

if __name__ == "__main__":
    reset_password()
