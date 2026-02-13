from database import SessionLocal
from models.turno import Turno
from models.paciente import Paciente
from models.agenda import Agenda
from models.practica import Practica, CategoriaPractica
from routers.exports import export_turnos
from datetime import date, datetime
import random

def reproduce_issue_v3():
    db = SessionLocal()
    turno = None
    paciente = None
    p1 = None
    p2 = None
    
    try:
        # 1. Crear datos de prueba
        agenda_id = 4 # Radioterapia Colombia
        
        # Generar DNI random para evitar colisiones
        rand_suffix = random.randint(1000, 9999)
        dni = f"99{rand_suffix}"
        
        # Crear Paciente Test
        paciente = Paciente(
            nombre="Mirta Elena",
            apellido="Nuñez Test",
            dni=dni,
            fecha_nacimiento=date(1980, 1, 1),
            telefono="111111",
            email=f"test{rand_suffix}@test.com"
        )
        db.add(paciente)
        
        # Crear Prácticas Dummy (sin agenda_id ni duracion)
        p_name_1 = f"PRACTICA 1 {rand_suffix}"
        p_name_2 = f"PRACTICA 2 {rand_suffix}"
        
        p1 = Practica(nombre=p_name_1, categoria=CategoriaPractica.RADIOTERAPIA)
        db.add(p1)
        
        p2 = Practica(nombre=p_name_2, categoria=CategoriaPractica.RADIOTERAPIA)
        db.add(p2)
        db.commit()
        
        # Crear Turno
        fecha_turno = datetime(2026, 1, 29, 10, 45)
        turno = Turno(
            fecha=fecha_turno,
            hora="10:45",
            paciente_id=paciente.id,
            agenda_id=agenda_id,
            estado="agendado"
        )
        db.add(turno)
        db.commit()
        
        # ASOCIAR DOS PRACTICAS
        turno.practicas.append(p1)
        turno.practicas.append(p2)
        db.commit()
        
        print(f"Creado Turno ID {turno.id} para {paciente.apellido} con 2 prácticas: {p1.nombre}, {p2.nombre}")
        
        # 2. Ejecutar lógica de exportación
        print("\n--- Ejecutando Exportación ---")
        results = export_turnos(
            desde=date(2026, 1, 29),
            hasta=date(2026, 1, 29),
            formato="json",
            db=db
        )
        
        print(f"\nResultados exportados para el día 2026-01-29: {len(results)}")
        count_nunez = 0
        for i, row in enumerate(results):
            # Filtramos solo nuestro paciente para no ver ruido
            if row['Paciente'] == "Nuñez Test, Mirta Elena":
                count_nunez += 1
                print(f"Fila {i+1}: {row['Paciente']} | Práctica: {row['Práctica']} | Tipo: {row['Tipo']}")
                
        print(f"\nTotal filas para 'Nuñez Test, Mirta Elena': {count_nunez}")

        # 3. Limpieza
        print("\n--- Limpiando datos ---")
        turno.practicas = []
        db.commit()
        
        db.delete(turno)
        db.delete(paciente)
        db.delete(p1)
        db.delete(p2)
        db.commit()
        print("Limpieza completada.")

    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
        # Intentar limpieza de emergencia
        if turno: db.delete(turno)
        if paciente: db.delete(paciente)
        if p1: db.delete(p1)
        if p2: db.delete(p2)
        try:
             db.commit()
        except:
             pass
    finally:
        db.close()

if __name__ == "__main__":
    reproduce_issue_v3()
