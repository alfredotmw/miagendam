
import sqlite3
import pandas as pd

def check_db():
    conn = sqlite3.connect('agendas.db')
    cursor = conn.cursor()
    
    print("\n--- 1. Table Info (Schema) ---")
    cursor.execute("PRAGMA table_info(users)")
    columns = cursor.fetchall()
    for col in columns:
        print(col)
        
    print("\n--- 2. ID of 'Alfredo' ---")
    try:
        cursor.execute("SELECT id, username, role, allowed_agendas FROM users WHERE username='Alfredo'")
        user = cursor.fetchone()
        print(f"User: {user}")
    except Exception as e:
        print(f"Error fetching user: {e}")

    conn.close()

if __name__ == "__main__":
    check_db()
