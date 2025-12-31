
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
import json
import io
import traceback
from typing import Any

from database import get_db, engine
from auth.jwt import get_current_user

# Import critical models for serialization (optional if using raw SQL, but safer with ORM)
from models.paciente import Paciente
from models.turno import Turno
from models.historia_clinica import HistoriaClinica
from models.radioterapia import SeguimientoRadioterapia
from models.user import User
from models.agenda import Agenda
from models.medico import MedicoDerivante

router = APIRouter(
    prefix="/backup",
    tags=["Backup"],
)

# Helper to serialize datetime
def json_serial(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    # Also handle date objects
    if hasattr(obj, 'isoformat'):
        return obj.isoformat()
    raise TypeError (f"Type {type(obj)} not serializable")

@router.get("/download")
def download_backup(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Generates a full JSON dump of the critical tables.
    Only ADMINs can access this.
    """
    if current_user['role'] != 'ADMIN':
        raise HTTPException(status_code=403, detail="Requiere privilegios de Administrador")

    print(f"🔄 INICIANDO BACKUP MANUAL solicitado por {current_user['username']}")

    try:
        # Define tables to dump
        # Using raw SQL or ORM? ORM is cleaner but slower for huge DBs.
        # For this scale (~10k records), ORM to dict is fine and safer.
        
        backup_data = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "generated_by": current_user['username'],
                "version": "1.0"
            },
            "pacientes": [],
            "turnos": [],
            "historia_clinica": [],
            "seguimiento_radioterapia": [],
            "medicos_derivantes": [],
            "users": [],
            "agendas": []
        }

        # Fetch Data
        # 1. Patients
        pacientes = db.query(Paciente).all()
        for p in pacientes:
            # Simple dict convention or use Pydantic? 
            # Manual dict is safest to avoid circular refs or extra fields
            p_dict = {c.name: getattr(p, c.name) for c in p.__table__.columns}
            backup_data["pacientes"].append(p_dict)

        # 2. Turnos
        turnos = db.query(Turno).all()
        for t in turnos:
            t_dict = {c.name: getattr(t, c.name) for c in t.__table__.columns}
            # Handle relationship fields manually if needed, usually FKs are in columns
            # t_dict['practicas_ids'] = ... ? The columns have FKs, but many-to-many?
            # TurnoPractica is a separate table.
            backup_data["turnos"].append(t_dict)
        
        # 2.5 TurnoPracticas (Important!)
        # Let's just dump raw table for many-to-many
        tps = db.execute(text("SELECT * FROM turnos_practicas")).fetchall()
        backup_data["turnos_practicas"] = [dict(row._mapping) for row in tps]

        # 3. Clinical History
        hcs = db.query(HistoriaClinica).all()
        for h in hcs:
            h_dict = {c.name: getattr(h, c.name) for c in h.__table__.columns}
            backup_data["historia_clinica"].append(h_dict)

        # 4. Radiotherapy Tracking
        segs = db.query(SeguimientoRadioterapia).all()
        for s in segs:
            s_dict = {c.name: getattr(s, c.name) for c in s.__table__.columns}
            backup_data["seguimiento_radioterapia"].append(s_dict)

        # 5. Medicos
        meds = db.query(MedicoDerivante).all()
        for m in meds:
            m_dict = {c.name: getattr(m, c.name) for c in m.__table__.columns}
            backup_data["medicos_derivantes"].append(m_dict)
        
        # 6. Users (Exclude password hashes? Maybe keep for full restore)
        users = db.query(User).all()
        for u in users:
            u_dict = {c.name: getattr(u, c.name) for c in u.__table__.columns}
            backup_data["users"].append(u_dict)

        # 7. Agendas
        agendas = db.query(Agenda).all()
        for a in agendas:
            a_dict = {c.name: getattr(a, c.name) for c in a.__table__.columns}
            backup_data["agendas"].append(a_dict)

        
        # Serialize to JSON Strings
        json_str = json.dumps(backup_data, default=json_serial, indent=2)
        
        # Create file-like object
        stream = io.StringIO(json_str)

        # Filename
        filename = f"backup_miagenda_{datetime.now().strftime('%Y%m%d_%H%M')}.json"

        # Return Streaming Response
        response = StreamingResponse(
            iter([stream.getvalue()]),
            media_type="application/json"
        )
        response.headers["Content-Disposition"] = f"attachment; filename={filename}"
        return response

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error generando backup: {str(e)}")
