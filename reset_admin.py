from sqlalchemy.orm import Session
from database import SessionLocal
from models.user import User, UserRole
import bcrypt

def reset_admin():
    db = SessionLocal()
    username = "Alfredo"
    new_password = "1234"
    
    user = db.query(User).filter_by(username=username).first()
    
    hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    if user:
        print(f"🔄 Usuario {username} encontrado. Reseteando contraseña...")
        user.password = hashed_password
        user.role = UserRole.ADMIN # Asegurar que sea admin
    else:
        print(f"➕ Usuario {username} no encontrado. Creándolo...")
        user = User(username=username, password=hashed_password, role=UserRole.ADMIN)
        db.add(user)
    
    db.commit()
    print(f"✅ Contraseña de '{username}' establecida a '{new_password}'.")
    db.close()

if __name__ == "__main__":
    reset_admin()
