import sqlite3
from datetime import datetime, date

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import SQLALCHEMY_DATABASE_URL
from models.paciente import Paciente
from models.turno import Turno
from models.agenda import Agenda
from models.practica import Practica
from models.radioterapia import SeguimientoRadioterapia
from routers.radioterapia import check_and_autofill


engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def verify_cycles():
    db = SessionLocal()
    try:
        # Create Dummy Patient
        new_paciente = Paciente(
            nombre="TEST_RADIO_CYCLES",
            apellido="PACIENTE",
            dni="9988776655",
            fecha_nacimiento=date(1980, 1, 1),
            telefono="123"
        )
        db.add(new_paciente)
        db.commit()
        db.refresh(new_paciente)
        paciente_id = new_paciente.id
        print(f"Created Patient {paciente_id}")

        # Need Agenda IDs for Consultation, Tac, Radiotherapy
        # Assuming Agenda names exist, but let's query them properly based on IDs
        agenda_tomo = db.query(Agenda).filter(Agenda.tipo == 'TOMOGRAFIA').first()
        agenda_radio = db.query(Agenda).filter(Agenda.tipo == 'RADIOTERAPIA').first()
        agenda_consulta = db.query(Agenda).filter(Agenda.nombre.like("%DUARTE%")).first()

        if not agenda_radio: 
            print("Missing Radioterapia agenda")
            return
            
        print(f"Agenda Tomo ID: {agenda_tomo.id if agenda_tomo else None}")
        print(f"Agenda Radio ID: {agenda_radio.id}")
        print(f"Agenda Consulta ID: {agenda_consulta.id if agenda_consulta else None}")

        # --- CYCLE 1 (Historical) ---
        print("\n--- Creating Cycle 1 (Historical) ---")
        t_cons_1 = Turno(paciente_id=paciente_id, agenda_id=agenda_consulta.id if agenda_consulta else 1, fecha=datetime(2023, 1, 10, 10, 0), hora="10:00:00", duracion=15, estado="COMPLETADO")
        t_tac_1 = Turno(paciente_id=paciente_id, agenda_id=agenda_tomo.id if agenda_tomo else 1, fecha=datetime(2023, 1, 15, 10, 0), hora="10:00:00", duracion=15, estado="COMPLETADO")
        t_ini_1 = Turno(paciente_id=paciente_id, agenda_id=agenda_radio.id, fecha=datetime(2023, 2, 1, 10, 0), hora="10:00:00", duracion=15, estado="COMPLETADO")
        t_fin_1 = Turno(paciente_id=paciente_id, agenda_id=agenda_radio.id, fecha=datetime(2023, 3, 1, 10, 0), hora="10:00:00", duracion=15, estado="COMPLETADO")

        db.add_all([t_cons_1, t_tac_1, t_ini_1, t_fin_1])
        db.commit()

        # Follow-up Row 1
        reg1 = SeguimientoRadioterapia(
            paciente_id=paciente_id,
             created_at=datetime(2023, 1, 1, 10, 0),
             fecha_consulta=date(2023, 1, 10)
        )
        db.add(reg1)
        db.commit()
        db.refresh(reg1)
        
        check_and_autofill(reg1, db)
        print(f"Cycle 1 autofilled: TAC={reg1.fecha_tac}, Ini={reg1.fecha_inicio}, Fin={reg1.fecha_fin}")
        assert reg1.fecha_tac == date(2023, 1, 15)
        assert reg1.fecha_inicio == date(2023, 2, 1)
        assert reg1.fecha_fin == date(2023, 3, 1)


        # --- CYCLE 2 (Current) ---
        print("\n--- Creating Cycle 2 (Current) ---")
        t_cons_2 = Turno(paciente_id=paciente_id, agenda_id=agenda_consulta.id if agenda_consulta else 1, fecha=datetime(2024, 5, 10, 10, 0), hora="10:00:00", duracion=15, estado="COMPLETADO")
        t_tac_2 = Turno(paciente_id=paciente_id, agenda_id=agenda_tomo.id if agenda_tomo else 1, fecha=datetime(2024, 5, 15, 10, 0), hora="10:00:00", duracion=15, estado="COMPLETADO")
        t_ini_2 = Turno(paciente_id=paciente_id, agenda_id=agenda_radio.id, fecha=datetime(2024, 6, 1, 10, 0), hora="10:00:00", duracion=15, estado="COMPLETADO")
        t_fin_2 = Turno(paciente_id=paciente_id, agenda_id=agenda_radio.id, fecha=datetime(2024, 7, 1, 10, 0), hora="10:00:00", duracion=15, estado="COMPLETADO")
        
        db.add_all([t_cons_2, t_tac_2, t_ini_2, t_fin_2])
        db.commit()

        # Follow-up Row 2
        reg2 = SeguimientoRadioterapia(
            paciente_id=paciente_id,
             created_at=datetime(2024, 5, 1, 10, 0),
             fecha_consulta=date(2024, 5, 10)
        )
        db.add(reg2)
        db.commit()
        db.refresh(reg2)
        
        # Test boundaries logic (Should only pick 2024 ones, even though 2023 exist and are earlier, 
        # and we use 100 limit so we could pick the 2023 end date if cycle boundary was not working)
        # Actually first is asc. If boundary logic fails, the first TAC globally is 2023, so `first_tac` would be 2023
        check_and_autofill(reg2, db)
        print(f"Cycle 2 autofilled: TAC={reg2.fecha_tac}, Ini={reg2.fecha_inicio}, Fin={reg2.fecha_fin}")
        assert reg2.fecha_tac == date(2024, 5, 15), "Cycle 2 picked old TAC"
        assert reg2.fecha_inicio == date(2024, 6, 1), "Cycle 2 picked old INICIO"
        assert reg2.fecha_fin == date(2024, 7, 1), "Cycle 2 picked wrong FIN"

        # Check reg1 again to make sure it doesn't pick cycle 2 dates for FIN
        # Remove Fin from reg1 artificially to trigger auto-fill again
        reg1.fecha_fin = None
        db.commit()
        check_and_autofill(reg1, db)
        print(f"Cycle 1 Re-autofilled FIN: {reg1.fecha_fin}")
        assert reg1.fecha_fin == date(2023, 3, 1), "Cycle 1 picked Future FIN (Boundary Failed!)"

        print("\nVerification SUCCESS! Cycles are insulated.")

    except Exception as e:
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        # Cleanup
        db.query(Turno).filter(Turno.paciente_id == paciente_id).delete()
        db.query(SeguimientoRadioterapia).filter(SeguimientoRadioterapia.paciente_id == paciente_id).delete()
        db.query(Paciente).filter(Paciente.id == paciente_id).delete()
        db.commit()
        db.close()

if __name__ == "__main__":
    verify_cycles()
