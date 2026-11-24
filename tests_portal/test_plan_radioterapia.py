"""Plan de radioterapia por cantidad de sesiones y feriados (base de prueba local).

Correr con DATABASE_URL apuntando a una base PostgreSQL VACÍA de prueba:
  DATABASE_URL=postgresql://.../miagendam_test python -m pytest tests_portal -q
"""
import os
from datetime import date, datetime

import pytest

if "miagendam_test" not in os.getenv("DATABASE_URL", ""):
    pytest.skip("Solo contra la base de prueba miagendam_test", allow_module_level=True)

from fastapi.testclient import TestClient  # noqa: E402

import main  # noqa: E402
from auth.jwt import get_current_user  # noqa: E402
from database import Base, SessionLocal, engine  # noqa: E402
from models import Agenda, Paciente, Practica, Turno  # noqa: E402
from routers.feriados import dias_de_tratamiento  # noqa: E402

USER = {"id": 1, "username": "admin", "role": "ADMIN", "allowed_agendas": None}


@pytest.fixture(scope="module")
def client():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    ag = Agenda(nombre="ACELERADOR LINEAL", tipo="RADIOTERAPIA", slot_minutos=10, activo=True)
    pr = db.query(Practica).first()
    if pr is None:
        pr = Practica(nombre="RADIOTERAPIA IMRT", categoria="RADIOTERAPIA")
        db.add(pr)
    pa = Paciente(nombre="PRUEBA", apellido="FICTICIO", dni="99000001")
    otro = Paciente(nombre="OTRO", apellido="FICTICIO", dni="99000002")
    db.add_all([ag, pa, otro])
    db.commit()
    # Ocupa el miércoles 2/12/2026 a las 08:00 con otro paciente.
    db.add(Turno(fecha=datetime(2026, 12, 2, 8, 0), hora="08:00:00", duracion=10, paciente_id=otro.id,
                 agenda_id=ag.id, estado="PENDIENTE"))
    db.commit()
    ids = {"agenda": ag.id, "practica": pr.id, "paciente": pa.id}
    db.close()
    main.app.dependency_overrides[get_current_user] = lambda: USER
    with TestClient(main.app) as c:
        c.ids = ids
        yield c
    main.app.dependency_overrides.clear()


def test_dias_habiles_sin_feriados():
    feriados = {date(2026, 12, 7): "Turístico", date(2026, 12, 8): "Inmaculada", date(2026, 12, 25): "Navidad"}
    dias = dias_de_tratamiento(date(2026, 12, 3), 5, feriados)
    # jue 3, vie 4, (sáb/dom), (lun 7 y mar 8 feriados), mié 9, jue 10, vie 11
    assert [d.day for d in dias] == [3, 4, 9, 10, 11]
    assert all(d.weekday() < 5 for d in dias)


def test_semilla_2026_y_plan(client):
    r = client.get("/feriados?anio=2026")
    assert r.status_code == 200 and len(r.json()) == 19
    plan = client.post("/turnos/plan-radioterapia", json={
        "agenda_id": client.ids["agenda"], "fecha_inicio": "2026-12-01", "sesiones": 25, "hora": "08:00",
        "practicas_ids": [client.ids["practica"]], "paciente_id": client.ids["paciente"], "duracion": 10})
    assert plan.status_code == 200, plan.text
    p = plan.json()
    fechas = [s["fecha"] for s in p["sesiones"]]
    assert len(fechas) == 25
    assert "2026-12-07" not in fechas and "2026-12-08" not in fechas and "2026-12-25" not in fechas
    assert all(date.fromisoformat(f).weekday() < 5 for f in fechas)
    assert p["desde"] == "2026-12-01"
    assert {f["fecha"] for f in p["feriados_salteados"]} >= {"2026-12-07", "2026-12-08", "2026-12-25"}
    ocupado = next(s for s in p["sesiones"] if s["fecha"] == "2026-12-02")
    assert ocupado["disponible"] is False and p["ocupados"] == 1
    assert 2027 in p["anios_sin_feriados"]   # el plan cruza a 2027 y no hay feriados cargados


def test_feriado_manual_y_desactivar(client):
    r = client.post("/feriados", json={"fecha": "2026-12-03", "nombre": "Mantenimiento del acelerador",
                                       "tipo": "sin_servicio"})
    assert r.status_code == 200 and r.json()["origen"] == "manual"
    plan = client.post("/turnos/plan-radioterapia", json={
        "agenda_id": client.ids["agenda"], "fecha_inicio": "2026-12-01", "sesiones": 3, "hora": "09:00",
        "practicas_ids": [client.ids["practica"]]}).json()
    assert [s["fecha"] for s in plan["sesiones"]] == ["2026-12-01", "2026-12-02", "2026-12-04"]
    fid = r.json()["id"]
    assert client.put(f"/feriados/{fid}/activo", json={"activo": False}).json()["activo"] is False
    plan = client.post("/turnos/plan-radioterapia", json={
        "agenda_id": client.ids["agenda"], "fecha_inicio": "2026-12-01", "sesiones": 3, "hora": "09:00",
        "practicas_ids": [client.ids["practica"]]}).json()
    assert [s["fecha"] for s in plan["sesiones"]] == ["2026-12-01", "2026-12-02", "2026-12-03"]


def test_solo_admin_modifica(client):
    main.app.dependency_overrides[get_current_user] = lambda: {**USER, "role": "RECEPCION"}
    try:
        assert client.post("/feriados", json={"fecha": "2026-12-10", "nombre": "Prueba"}).status_code == 403
        assert client.get("/feriados?anio=2026").status_code == 200
    finally:
        main.app.dependency_overrides[get_current_user] = lambda: USER


def test_limites(client):
    base = {"agenda_id": client.ids["agenda"], "fecha_inicio": "2026-12-01", "hora": "08:00",
            "practicas_ids": [client.ids["practica"]]}
    assert client.post("/turnos/plan-radioterapia", json={**base, "sesiones": 0}).status_code == 422
    assert client.post("/turnos/plan-radioterapia", json={**base, "sesiones": 61}).status_code == 422
