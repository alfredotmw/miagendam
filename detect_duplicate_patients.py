from database import SessionLocal
from models.paciente import Paciente
from sqlalchemy import func

def detect_duplicate_patients():
    db = SessionLocal()
    try:
        print("🔍 Buscando pacientes duplicados por DNI...")
        
        # Agrupar por DNI y contar
        query = db.query(
            Paciente.dni,
            func.count(Paciente.id).label('count')
        ).filter(
            Paciente.dni != None,
            Paciente.dni != ''
        ).group_by(
            Paciente.dni
        ).having(
            func.count(Paciente.id) > 1
        )
        
        duplicates = query.all()
        
        if not duplicates:
            print("✅ No se encontraron DNI duplicados.")
            return

        print(f"⚠️ Se encontraron {len(duplicates)} DNIs duplicados:\n")
        
        for dup in duplicates:
            dni = dup.dni
            count = dup.count
            
            print(f"🆔 DNI: {dni} | Cantidad: {count}")
            
            # Detalle de los pacientes
            pacientes = db.query(Paciente).filter(Paciente.dni == dni).all()
            
            for p in pacientes:
                print(f"   - ID: {p.id} | Nombre: {p.nombre} {p.apellido} | Creado (estimado): {p.id}")
            
            print("-" * 40)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    detect_duplicate_patients()
