from sqlalchemy.orm import Session
from database import SessionLocal
from models.agenda import Agenda
from models.practica import Practica, CategoriaPractica
from models.agenda_practica import AgendaPractica

def upgrade_tac_agenda():
    db = SessionLocal()
    print("--- 🏥 UPGRADE: TAC DE MARCACION ---")

    # 1. Crear Práctica TAC DE MARCACION
    p_name = "TAC DE MARCACION"
    practica = db.query(Practica).filter(Practica.nombre == p_name).first()
    
    if not practica:
        print(f"➕ Creando Práctica: {p_name}")
        # Asignamos categoría TOMOGRAFIA
        practica = Practica(nombre=p_name, categoria=CategoriaPractica.TOMOGRAFIA)
        db.add(practica)
        db.commit()
        db.refresh(practica)
    else:
        print(f"✅ Práctica existente: {practica.nombre}")

    # 2. Crear Agenda "TAC DE MARCACION"
    # El usuario pidió "COMO SI FUERA UN SERVICIO MAS", así que creamos una Agenda dedicada.
    a_name = "TAC DE MARCACION"
    agenda = db.query(Agenda).filter(Agenda.nombre == a_name).first()

    if not agenda:
        print(f"➕ Creando Agenda: {a_name}")
        agenda = Agenda(
            nombre=a_name,
            tipo="TOMOGRAFIA", # Usamos tipo TOMOGRAFIA para que reutilice lógica de duración y slots
            profesional=None
        )
        db.add(agenda)
        db.commit()
        db.refresh(agenda)
    else:
        print(f"✅ Agenda existente: {agenda.nombre}")

    # 3. Vincular Agenda -> Práctica
    link = db.query(AgendaPractica).filter(
        AgendaPractica.agenda_id == agenda.id,
        AgendaPractica.practica_id == practica.id
    ).first()

    if not link:
        print(f"🔗 Vinculando: {agenda.nombre} -> {practica.nombre}")
        new_link = AgendaPractica(agenda_id=agenda.id, practica_id=practica.id)
        db.add(new_link)
        db.commit()
    else:
        print("🔗 Vinculación ya existe.")

    db.close()
    print("✅ Upgrade completado exitosamente.")

if __name__ == "__main__":
    upgrade_tac_agenda()
