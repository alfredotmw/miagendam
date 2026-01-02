from database import SessionLocal
from models.historia_clinica import HistoriaClinica
from sqlalchemy import desc

db = SessionLocal()

print("--- Últimas 5 Notas ---")
notas = db.query(HistoriaClinica).order_by(desc(HistoriaClinica.id)).limit(5).all()

for nota in notas:
    print(f"\nID: {nota.id} | Paciente ID: {nota.paciente_id} | Servicio: {nota.servicio}")
    print(f"  Motivo: {nota.motivo_consulta[:50] if nota.motivo_consulta else 'None'}")
    
    # Check users
    creador = nota.creado_por.username if nota.creado_por else "NONE"
    medico = nota.medico.username if nota.medico else "NONE"
    firmante = nota.firmado_por.username if nota.firmado_por else "NONE"
    
    print(f"  Creado Por ID: {nota.creado_por_id} ({creador})")
    print(f"  Medico ID: {nota.medico_id} ({medico})")
    print(f"  Firmado Por ID: {nota.firmado_por_id} ({firmante})")

db.close()
