from database import SessionLocal
from models.paciente import Paciente

def normalize_existing_dnis():
    db = SessionLocal()
    try:
        print("🔍 Normalizando DNIs en la base de datos...")
        pacientes = db.query(Paciente).all()
        count = 0
        errores = 0
        
        for p in pacientes:
            if p.dni:
                original_dni = p.dni
                # Eliminar puntos, espacios y guiones
                nuevo_dni = original_dni.replace('.', '').replace(' ', '').replace('-', '').strip()
                
                if original_dni != nuevo_dni:
                    try:
                        # Verificar si el nuevo DNI ya existe en OTRO paciente (conflicto)
                        existing_collision = db.query(Paciente).filter(Paciente.dni == nuevo_dni, Paciente.id != p.id).first()
                        
                        if existing_collision:
                            print(f"⚠️ CONFLICTO: No se puede normalizar Paciente ID {p.id} ({original_dni} -> {nuevo_dni}). Ya existe otro paciente ID {existing_collision.id} con ese DNI.")
                            errores += 1
                        else:
                            p.dni = nuevo_dni
                            count += 1
                            print(f"✅ ID {p.id}: {original_dni} -> {nuevo_dni}")
                    except Exception as e:
                        print(f"❌ Error procesando ID {p.id}: {e}")
                        errores += 1
        
        if count > 0:
            db.commit()
            print(f"\n✨ Se actualizaron {count} pacientes correctamente.")
        else:
            print("\n👍 Todos los DNIs ya estaban normalizados (o hubo conflictos que impidieron cambios).")
            
        if errores > 0:
            print(f"⚠️ Hubo {errores} conflictos/errores manuales requeridos.")

    except Exception as e:
        db.rollback()
        print(f"Error General: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    normalize_existing_dnis()
