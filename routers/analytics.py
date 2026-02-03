from fastapi import APIRouter, Depends, HTTPException, Query
from auth.jwt import SECRET_KEY, ALGORITHM, get_current_user
from typing import Optional
from models.medico import MedicoDerivante
from sqlalchemy.orm import Session
from database import get_db
from models.turno import Turno
from models.paciente import Paciente
from models.agenda import Agenda
from models.practica import Practica
from models.medico import MedicoDerivante
from models.turno_practica import TurnoPractica
import pandas as pd
from datetime import date

router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"],
)

def normalize_service(agenda_name, practices_names=None):
    name = agenda_name.upper()
    
    # 🟢 1. Lógica Radioterapia con Sede
    if "RADIOTERAPIA" in name or "LINAC" in name:
        if "SAN MARTIN" in name or "SM" in name:
            return "RADIOTERAPIA SM"
        if "COLOMBIA" in name or "COL" in name:
            return "RADIOTERAPIA COL"
        return "RADIOTERAPIA (GEN)"

    # 🟢 2. Lógica Robusta Tomografía vs RX (Mirando Prácticas si es posible)
    # Copiamos lógica de exports.py para coherencia
    if practices_names:
        # Si hay prácticas, tratamos de deducir por el contenido
        # Concatenamos para buscar keywords en el conjunto
        full_practice_str = " ".join(practices_names).upper()
        
        # 🟢 2.1 Excepción TAC DE MARCACIÓN (Pedido explícito para separar en métricas)
        if "TAC DE MARCACIÓN" in full_practice_str or "TAC DE MARCACION" in full_practice_str:
            return "TAC ACL"
        
        if any(k in full_practice_str for k in ["RADIOGRAFIA", "RX", "PLACA", "ESPINOGRAMA", "INCIDENCIA", "MAMOGRAFIA", "DENSITOMETRIA", "UROGRAMA", "TELEGONO"]):
            return "RADIOGRAFIA"
        
        if any(k in full_practice_str for k in ["TOMOGRAFIA", "TC ", " TC", "TAC ", " TAC", "UROTAC", "ANGIOTC", "SCORE DE CALCIO"]):
            return "TOMOGRAFIA"

    # Fallback a Nombre de Agenda si no detectamos nada o no hay prácticas
    if "TOMOGRAFIA" in name or "TAC" in name: return "TOMOGRAFIA"
    if "QUIMIOTERAPIA" in name or "QUIMIO" in name:
        if "SAN MARTIN" in name or "SM" in name:
            return "QUIMIOTERAPIA SM"
        if "COLOMBIA" in name or "COL" in name:
            return "QUIMIOTERAPIA COL"
        return "QUIMIOTERAPIA"
    if "CAMARA GAMMA" in name or "MN" in name or "MEDICINA NUCLEAR" in name or "SPECT" in name: return "MEDICINA NUCLEAR"
    if "ECOGRAFIA" in name or "ECO" in name: return "ECOGRAFIA"
    if "PET" in name: return "PET"
    if "CONSULTORIO" in name: return "CONSULTORIOS"
    if "RADIOGRAFIA" in name or "RX" in name: return "RADIOGRAFIA"
    if "ELECTRO" in name or "MAPEO" in name or "EEG" in name: return "ELECTRO Y MAPEOS"
    
    return "OTROS"

@router.get("/live_data")
def get_live_data(db: Session = Depends(get_db)):
    """
    Retorna un JSON plano optimizado para Excel Power Query (Datos -> Desde Web).
    Formato solicitado:
    1. Fecha (dd/mm/yyyy)
    2. Hora (hh:mm:ss)
    3. DNI
    4. Paciente
    5. Obra Social
    6. Sexo
    7. Edad
    8. Estudio Solicitado (una fila por práctica)
    9. Servicio
    10. Estado
    """
    # Query con Joins para obtener una fila por práctica (Explode)
    results = db.query(Turno, Practica).join(TurnoPractica, Turno.id == TurnoPractica.turno_id).join(Practica, TurnoPractica.practica_id == Practica.id).all()
    
    data = []
    for turno, practica in results:
        # Calcular edad
        edad = None
        if turno.paciente.fecha_nacimiento:
            hoy = date.today()
            fn = turno.paciente.fecha_nacimiento
            edad = hoy.year - fn.year - ((hoy.month, hoy.day) < (fn.month, fn.day))

        # Formatear Hora (hh:mm:ss)
        hora_fmt = turno.hora
        if len(hora_fmt) == 5: # "09:00" -> "09:00:00"
            hora_fmt += ":00"

        row = {
            "Fecha": turno.fecha.strftime("%d/%m/%Y"),
            "Hora": hora_fmt,
            "DNI": turno.paciente.dni,
            "Paciente": f"{turno.paciente.apellido}, {turno.paciente.nombre}",
            "Celular": turno.paciente.celular if (turno.paciente and turno.paciente.celular) else (turno.paciente.telefono if (turno.paciente and turno.paciente.telefono) else "N/A"),
            "Obra Social": turno.paciente.obra_social.nombre if turno.paciente.obra_social else "N/A",
            "Sexo": turno.paciente.sexo,
            "Edad": edad,
            "Estudio Solicitado": practica.nombre,
            "Servicio": turno.agenda.nombre,
            "Médico Solicitante": turno.medico_derivante.nombre if turno.medico_derivante else "N/A",
            "Estado": turno.estado
        }
        data.append(row)

    return data

@router.get("/download")
def download_excel(db: Session = Depends(get_db)):
    """
    Genera y descarga un archivo Excel con los datos actuales.
    """
    # Reutilizamos la lógica de live_data para obtener los datos
    data = get_live_data(db)
    
    # Crear DataFrame
    df = pd.DataFrame(data)
    
    # Guardar en un archivo temporal (o en memoria)
    file_path = "reporte_agendas.xlsx"
    df.to_excel(file_path, index=False)
    
    from fastapi.responses import FileResponse
    return FileResponse(path=file_path, filename="Reporte_Agendas_Medicas.xlsx", media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

@router.get("/excel_feed")
def get_excel_feed(
    token: str = Query(..., description="JWT Token for authentication"),
    db: Session = Depends(get_db)
):
    # Verify Token manually (query param auth for Excel)
    try:
        from jose import jwt, JWTError # Fix imports if needed inside processing or global
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if "sub" not in payload:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    # Query all turns
    # We join with relevant tables to optimize fetching
    turnos = db.query(Turno).join(Paciente).join(Agenda).outerjoin(Turno.medico_derivante).order_by(Turno.fecha.desc()).all()
    
    data = []
    for t in turnos:
        # Calculate Age
        edad = t.paciente.edad
        
        # Format Date and Time
        fecha_str = t.fecha.strftime("%Y-%m-%d") if t.fecha else ""
        hora_str = t.hora
        
        # Determine Status
        estado = t.estado
        
        # Determine Referral
        derivante = t.medico_derivante.nombre if t.medico_derivante else ""
        
        # Build Record
        record = {
            "ID_Turno": t.id,
            "Fecha": fecha_str,
            "Hora": hora_str,
            "Semana": t.fecha.isocalendar()[1] if t.fecha else "",
            "Mes": t.fecha.month if t.fecha else "",
            "Año": t.fecha.year if t.fecha else "",
            "Paciente": f"{t.paciente.apellido}, {t.paciente.nombre}",
            "DNI": t.paciente.dni,
            "Edad": edad,
            "Obra_Social": t.paciente.obra_social.nombre if t.paciente.obra_social else "",
            "Agenda_Servicio": t.agenda.nombre,
            "Estado": estado,
            "Medico_Derivante": derivante,
            "Patologia": t.patologia or "",
            # Include Practices?
            "Practicas": ", ".join([p.nombre for p in t.practicas]) if t.practicas else ""
        }
        data.append(record)
        
    return data

@router.get("/dashboard")
def get_dashboard_data(
    start_date: Optional[str] = Query(None), # YYYY-MM-DD
    end_date: Optional[str] = Query(None),   # YYYY-MM-DD
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user) # Secure: Admin check needed?
):
    # Security Check (Optional strict admin check here or rely on frontend hiding)
    # if current_user['role'] != 'ADMIN': raise ...
    
    from sqlalchemy import func, distinct, case
    from datetime import datetime
    
    # Base Query
    # 🟢 FIX: Use DISTINCT to avoid double counting if multiple practices or joins multiply rows
    query = db.query(Turno).distinct().join(Agenda).join(Paciente).outerjoin(Turno.medico_derivante).outerjoin(TurnoPractica).outerjoin(Practica)
    
    if start_date:
        query = query.filter(Turno.fecha >= start_date)
    if end_date:
         # Add time 23:59:59 to end_date if it's just YYYY-MM-DD string comparison logic handling
         # But usually string compare works if format matches. Safe:
         query = query.filter(Turno.fecha <= f"{end_date} 23:59:59")

    turnos = query.all()
    
    # Python-side Aggregation (Easier for complex "Service" normalization than purely SQL)
    
    stats = {
        "dates_label": [],
        "timeline_counts": {},
        
        "services": {}, # key: service_name -> { total_practices, unique_patients, completed, absent, os_counts: {}, medico_counts: {} }
    }
    
    # Structures for counting
    # distinct_patients[service] = set(patient_id)
    distinct_patients = {}
    
    # Radiotherapy specific (Turno level) aggregation for the dedicated cards
    # Radiotherapy specific (Turno level) aggregation for the dedicated cards
    radio_daily_stats = {
         "SAN MARTIN": {}, # date string -> { completed: 0, absent: 0 }
         "COLOMBIA": {}
    }

    for t in turnos:
        # Extraer nombres de prácticas para mejor clasificación
        p_names = [p.nombre for p in t.practicas] if t.practicas else []
        
        # Determine Service
        svc = normalize_service(t.agenda.nombre, p_names)
        
        # Skip Consultorios and Otros for main stats if requested
        if svc in ["CONSULTORIOS", "OTROS"]:
            continue

        if svc not in stats["services"]:
            stats["services"][svc] = {
                "practices": 0,
                "completed": 0,
                "absent": 0,
                "os_counts": {},
                "medico_counts": {},
            }
            distinct_patients[svc] = {
                "completed": set(),
                "absent": set()
            }

        # Count Practices
        p_count = len(t.practicas) if t.practicas else 1
        stats["services"][svc]["practices"] += p_count
        
        # Status
        st = t.estado.upper()
        if st == "COMPLETADO":
            stats["services"][svc]["completed"] += p_count
            distinct_patients[svc]["completed"].add(t.paciente_id)
        elif st == "AUSENTE" or st == "PENDIENTE": # 👈 PENDIENTE counts as AUSENTE for metrics
            stats["services"][svc]["absent"] += p_count
            distinct_patients[svc]["absent"].add(t.paciente_id)
        
        # OS & Medico
        os_name = t.paciente.obra_social.nombre if t.paciente.obra_social else "PARTICULAR"
        stats["services"][svc]["os_counts"][os_name] = stats["services"][svc]["os_counts"].get(os_name, 0) + 1
        
        med_name = t.medico_derivante.nombre if t.medico_derivante else "NO ESPECIFICADO"
        stats["services"][svc]["medico_counts"][med_name] = stats["services"][svc]["medico_counts"].get(med_name, 0) + 1
        
        # Special Logic for Radiotherapy (Legacy/Dedicated Cards Support)
        # We still want the old Sede-specific counters for the bottom cards, 
        # even if we now have them in the main chart too.
        if "RADIOTERAPIA" in t.agenda.nombre.upper():
            sede = "UNKNOWN"
            if "SAN MARTIN" in t.agenda.nombre.upper() or "SM" in t.agenda.nombre.upper():
                sede = "SAN MARTIN"
            elif "COLOMBIA" in t.agenda.nombre.upper():
                sede = "COLOMBIA"
            
            if sede in radio_daily_stats:
                d_str = t.fecha.strftime("%Y-%m-%d")
                if d_str not in radio_daily_stats[sede]:
                    radio_daily_stats[sede][d_str] = {"completed": 0, "absent": 0}
                
                if st == "COMPLETADO":
                    radio_daily_stats[sede][d_str]["completed"] += 1
                elif st == "AUSENTE" or st == "PENDIENTE":
                     radio_daily_stats[sede][d_str]["absent"] += 1

    # Finalize Services Data
    final_data = []
    
    for svc, data in stats["services"].items():
        total_turnos_validos = data["completed"] + data["absent"] 
        absent_rate = 0
        if total_turnos_validos > 0:
            absent_rate = round((data["absent"] / total_turnos_validos) * 100, 1)
            
        top_os = sorted(data["os_counts"].items(), key=lambda x: x[1], reverse=True)[:10]
        top_med = sorted(data["medico_counts"].items(), key=lambda x: x[1], reverse=True)[:10]
        
        final_data.append({
            "service": svc,
            "practices_count": data["practices"],
            "patients_completed": len(distinct_patients[svc]["completed"]),
            "patients_absent": len(distinct_patients[svc]["absent"]),
            "patients_total_unique": len(distinct_patients[svc]["completed"] | distinct_patients[svc]["absent"]),
            "completed": data["completed"],
            "absent": data["absent"],
            "absentism_rate": absent_rate,
            "top_os": top_os,
            "top_medicos": top_med
        })
        
    # Radiotherapy Stats (Detailed from SeguimientoRadioterapia)
    from models.radioterapia import SeguimientoRadioterapia
    
    # helper for aggregations
    def get_radio_aggregations(sede_filter):
        q = db.query(SeguimientoRadioterapia)
        if sede_filter:
            q = q.filter(SeguimientoRadioterapia.sede.ilike(f"%{sede_filter}%"))
        
        all_recs = q.all()
        
        patologias = {}
        obras_sociales = {}
        derivantes = {}
        starts_by_month = {}
        ends_by_month = {}
        
        en_lista_count = 0
        
        for r in all_recs:
             # En Lista logic (simplified: if no end date -> active)
             if not r.fecha_fin:
                 en_lista_count += 1
                 
             # Patologia
             pat = r.patologia or "NO ESPECIFICADO"
             patologias[pat] = patologias.get(pat, 0) + 1
             
             # OS
             os = r.paciente.obra_social.nombre if r.paciente and r.paciente.obra_social else "PARTICULAR"
             obras_sociales[os] = obras_sociales.get(os, 0) + 1
             
             # Derivante
             der = r.medico_derivante or "NO ESPECIFICADO"
             derivantes[der] = derivantes.get(der, 0) + 1
             
             # Start/End Trends
             if r.fecha_inicio:
                 m_s = r.fecha_inicio.strftime("%Y-%m")
                 starts_by_month[m_s] = starts_by_month.get(m_s, 0) + 1
             if r.fecha_fin:
                 m_e = r.fecha_fin.strftime("%Y-%m")
                 ends_by_month[m_e] = ends_by_month.get(m_e, 0) + 1
                 
        # Normalize Trends
        all_months = sorted(list(set(starts_by_month.keys()) | set(ends_by_month.keys())))
        trend_data = []
        for m in all_months:
            trend_data.append({
                "month": m,
                "inicios": starts_by_month.get(m, 0),
                "finalizaciones": ends_by_month.get(m, 0)
            })
            
        return {
            "en_lista": en_lista_count,
            "patologias": sorted(patologias.items(), key=lambda x: x[1], reverse=True)[:15],
            "obras_sociales": sorted(obras_sociales.items(), key=lambda x: x[1], reverse=True)[:15],
            "derivantes": sorted(derivantes.items(), key=lambda x: x[1], reverse=True)[:15],
            "trends": trend_data
        }

    radio_full_stats = {
        "SAN MARTIN": {
             **get_radio_aggregations("San Martín"),
             "daily_attendance": [{"date": k, **v} for k, v in sorted(radio_daily_stats["SAN MARTIN"].items())]
        },
        "COLOMBIA": {
             **get_radio_aggregations("Colombia"),
             "daily_attendance": [{"date": k, **v} for k, v in sorted(radio_daily_stats["COLOMBIA"].items())]
        }
    }
    
    # Merge En Lista Aggregates for strict "En Lista" Chart (COL vs SM)
    en_lista_summary = {
        "COLOMBIA": radio_full_stats["COLOMBIA"]["en_lista"],
        "SAN MARTIN": radio_full_stats["SAN MARTIN"]["en_lista"]
    }

    final_response = {
        "services_data": final_data,
        "radiotherapy": radio_full_stats,
        "radio_en_lista_summary": en_lista_summary
    }
        
    return final_response
