from fastapi import APIRouter, Depends, Query, HTTPException, Response
from sqlalchemy.orm import Session
from database import get_db
from models.turno import Turno
from models.paciente import Paciente
from models.agenda import Agenda
from datetime import date
import csv
import io

router = APIRouter(prefix="/exports", tags=["Exports"])


@router.get("/turnos")
def export_turnos(
    desde: date = Query(..., description="Fecha desde (YYYY-MM-DD)"),
    hasta: date = Query(..., description="Fecha hasta (YYYY-MM-DD)"),
    formato: str = Query("json", description="Formato de salida: json o csv"),
    db: Session = Depends(get_db)
):
    """
    Exporta turnos entre fechas dadas.
    Permite formato JSON (por defecto) o CSV.
    """

    turnos = (
        db.query(Turno)
        .join(Paciente, Paciente.id == Turno.paciente_id)
        .join(Agenda, Agenda.id == Turno.agenda_id)
        .filter(Turno.fecha >= desde, Turno.fecha <= hasta) # Usar comparación directa o between
        .all()
    )

    if not turnos:
        raise HTTPException(status_code=404, detail="No hay turnos en el rango indicado")

    # 🧩 Transformar datos a lista de diccionarios
    data = []
    for t in turnos:
        paciente_nombre = f"{t.paciente.apellido}, {t.paciente.nombre}" if t.paciente else "Desconocido"
        
        # Priorizar celular, sino telefono
        contacto = t.paciente.celular if t.paciente and t.paciente.celular else (t.paciente.telefono if t.paciente else "")

        # Calcular edad si hay fecha_nacimiento
        edad_paciente = ""
        if t.paciente and t.paciente.fecha_nacimiento:
            hoy = date.today()
            nac = t.paciente.fecha_nacimiento
            # Cálculo simple de edad
            edad_paciente = hoy.year - nac.year - ((hoy.month, hoy.day) < (nac.month, nac.day))

        # Obtener médico derivante
        medico_derivante = t.medico_derivante.nombre if t.medico_derivante else ""

        # Patología: ya existe columna t.patologia
        patologia_val = t.patologia if t.patologia else ""

        # Día en letras (Español)
        dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        dia_str = dias_semana[t.fecha.weekday()]



        # 🧠 Lógica para separar Tomografía de Radiografía
        # Iteramos sobre las prácticas para generar una fila por CADA estudio
        items_a_exportar = []
        
        if t.practicas:
            for practica in t.practicas:
                # Determinar servicio específico para esta práctica
                p_nombre = practica.nombre.upper()
                servicio_item = t.agenda.nombre # Default
                
                # PRIORIDAD: Primero chequear RX/Radiografía para evitar falsos positivos de "TAC" en palabras como "CONTACTO" o "TORACICA" (si aplicara)
                # y "URO" en "UROGRAMA".
                if any(k in p_nombre for k in ["RADIOGRAFIA", "RX", "PLACA", "ESPINOGRAMA", "INCIDENCIA", "MAMOGRAFIA", "DENSITOMETRIA", "UROGRAMA", "TELEGONO"]):
                    servicio_item = "RADIOGRAFIA"
                elif any(k in p_nombre for k in ["TOMOGRAFIA", "TC ", " TC", "TAC ", " TAC", "UROTAC", "ANGIOTC", "SCORE DE CALCIO"]):
                    # Quitamos "TAC" (suelto) para evitar substrings peligrosos, usamos "TAC " o " TAC"
                    # Quitamos "URO" solo -> "UROTAC"
                    servicio_item = "TOMOGRAFIA"
                else: 
                     # Si no es ni Tomo ni RX, pero estamos en la agenda combinada, intentamos deducir
                     if "TOMOGRAFIA" in t.agenda.nombre.upper() and "RX" in t.agenda.nombre.upper():
                         # ESTRATEGIA: Si no matchea nada obvio, pero la agenda es MIXTA,
                         # vamos a intentar ser más laxos o simplemente marcarlo
                         servicio_item = "OTROS/SIN-CLASIFICAR"
                     else:
                        servicio_item = t.agenda.nombre


                items_a_exportar.append({
                    "practica_nombre": practica.nombre,
                    "servicio": servicio_item
                })
        else:
            # Si no tiene prácticas, mostramos una fila genérica
            items_a_exportar.append({
                "practica_nombre": "",
                "servicio": t.agenda.tipo # Usamos el TIPO de agenda como fallback seguro
            })

        for item in items_a_exportar:
            data.append({
                "Fecha": t.fecha.strftime("%Y-%m-%d"),
                "Día": dia_str,
                "Hora": t.hora,
                "Paciente": paciente_nombre,
                "DNI": t.paciente.dni if t.paciente else "",
                "Edad": edad_paciente,           
                "Celular": contacto,
                "Agenda": t.agenda.nombre if t.agenda else "", # ✅ Volvemos al nombre original de la Agenda
                "Tipo": item["servicio"],       # ✅ TIPO DE ESTUDIO (Tomografía, Radiografía, etc)
                "Medico Derivante": medico_derivante, 
                "Patologia": patologia_val,           
                "Estado": t.estado,
                "Duracion": t.duracion,
                "Práctica": item["practica_nombre"] # ✅ Una sola práctica por fila
            })

    # 📤 Exportar como JSON
    if formato.lower() == "json":
        return data

    # 📤 Exportar como CSV
    elif formato.lower() == "csv":
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)

        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=turnos_{desde}_{hasta}.csv"
            },
        )

    else:
        raise HTTPException(status_code=400, detail="Formato inválido. Use 'json' o 'csv'.")
