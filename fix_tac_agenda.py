from sqlalchemy.orm import Session
from database import SessionLocal
from models.agenda import Agenda
from models.practica import Practica
from models.agenda_practica import AgendaPractica

def fix_tac_agenda():
    db = SessionLocal()
    print("--- 🛠️ FIX: Revert TAC Agenda & Link to Tomography ---")

    # 1. Delete "TAC DE MARCACION" Agenda if exists
    wrong_agenda_name = "TAC DE MARCACION"
    wrong_agenda = db.query(Agenda).filter(Agenda.nombre == wrong_agenda_name).first()
    
    if wrong_agenda:
        print(f"🗑️ Eliminando Agenda incorrecta: {wrong_agenda_name}")
        # Delete links first (cascade usually handles this but safety first)
        db.query(AgendaPractica).filter(AgendaPractica.agenda_id == wrong_agenda.id).delete()
        db.delete(wrong_agenda)
        db.commit()
    else:
        print(f"ℹ️ La Agenda {wrong_agenda_name} no existe (o ya fue borrada).")

    # 2. Get "TOMOGRAFIAS Y RX" Agenda
    target_agenda_name = "TOMOGRAFIAS Y RX"
    target_agenda = db.query(Agenda).filter(Agenda.nombre == target_agenda_name).first()
    
    if not target_agenda:
        print(f"❌ Error: No se encontró la agenda {target_agenda_name}")
        return

    # 3. Get "TAC DE MARCACION" Practice
    p_name = "TAC DE MARCACION"
    practica = db.query(Practica).filter(Practica.nombre == p_name).first()

    if not practica:
        print(f"❌ Error: No se encontró la práctica {p_name}")
        # Fallback create if missing (though upgrade script created it)
        from models.practica import CategoriaPractica
        practica = Practica(nombre=p_name, categoria=CategoriaPractica.TOMOGRAFIA)
        db.add(practica)
        db.commit()
        db.refresh(practica)

    # 4. Link Practice to Target Agenda
    link = db.query(AgendaPractica).filter(
        AgendaPractica.agenda_id == target_agenda.id,
        AgendaPractica.practica_id == practica.id
    ).first()

    if not link:
        print(f"🔗 Vinculando: {target_agenda.nombre} -> {practica.nombre}")
        new_link = AgendaPractica(agenda_id=target_agenda.id, practica_id=practica.id)
        db.add(new_link)
        db.commit()
    else:
        print(f"✅ Vinculación ya existe: {target_agenda.nombre} -> {practica.nombre}")

    db.close()
    print("✅ Fix completado.")

if __name__ == "__main__":
    fix_tac_agenda()
