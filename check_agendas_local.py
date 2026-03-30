import sqlite3

def check_agendas():
    conn = sqlite3.connect('agendas.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre, tipo FROM agendas")
    agendas = cursor.fetchall()
    print("Agendas in database:")
    for a in agendas:
        print(f"ID: {a[0]}, Nombre: {a[1]}, Tipo: {a[2]}")
    conn.close()

if __name__ == "__main__":
    check_agendas()
