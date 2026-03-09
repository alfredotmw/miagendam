import sys
import os

from database import SessionLocal
from models.user import User
from models.agenda import Agenda

def check():
    db = SessionLocal()
    try:
        users = db.query(User).all()
        for u in users:
            print(f"User: {u.username}, Role: {u.role}, Agendas count: {len(u.agendas)}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check()
