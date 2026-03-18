import sqlite3

DB_PATH = "agendas.db"

def assign_specialties():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Give someone a non-oncology specialty
        # Assuming admin/testuser exists. Let's find one user.
        cursor.execute("SELECT id, username FROM users LIMIT 2")
        users = cursor.fetchall()
        
        if len(users) >= 2:
            print(f"Setting {users[0][1]} to 'Oncología'")
            cursor.execute("UPDATE users SET especialidad = 'Oncología' WHERE id = ?", (users[0][0],))
            
            print(f"Setting {users[1][1]} to 'Cardiología'")
            cursor.execute("UPDATE users SET especialidad = 'Cardiología' WHERE id = ?", (users[1][0],))

            conn.commit()
            print("Test users updated successfully.")
        else:
            print("Not enough users to test both scenarios.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    assign_specialties()
