
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
        
        if any(k in full_practice_str for k in ["RADIOGRAFIA", "RX", "PLACA", "ESPINOGRAMA", "INCIDENCIA", "MAMOGRAFIA", "DENSITOMETRIA", "UROGRAMA", "TELEGONO"]):
            return "RADIOGRAFIA"
        
        if any(k in full_practice_str for k in ["TOMOGRAFIA", "TC ", " TC", "TAC ", " TAC", "UROTAC", "ANGIOTC", "SCORE DE CALCIO"]):
            return "TOMOGRAFIA"

    # Fallback a Nombre de Agenda si no detectamos nada o no hay prácticas
    if "TOMOGRAFIA" in name or "TAC" in name: return "TOMOGRAFIA"
    if "CAMARA GAMMA" in name or "MN" in name or "MEDICINA NUCLEAR" in name or "SPECT" in name: return "MEDICINA NUCLEAR"
    if "ECOGRAFIA" in name or "ECO" in name: return "ECOGRAFIA"
    if "PET" in name: return "PET"
    if "CONSULTORIO" in name: return "CONSULTORIOS"
    if "RADIOGRAFIA" in name or "RX" in name: return "RADIOGRAFIA"
    
    return "OTROS"

def test_normalization():
    print("Testing Normalization Logic...")
    
    # Test Radiotherapy
    assert normalize_service("RADIOTERAPIA SM") == "RADIOTERAPIA SM"
    assert normalize_service("LINAC COLOMBIA") == "RADIOTERAPIA COL"
    
    # Test Tomography vs RX
    assert normalize_service("TOMOGRAFIA", ["UROTAC"]) == "TOMOGRAFIA"
    assert normalize_service("GENERICO", ["MAMOGRAFIA"]) == "RADIOGRAFIA"
    assert normalize_service("TOMOGRAFIA", ["PLACA TORAX"]) == "RADIOGRAFIA" # Hybrid case
    
    print("✅ All Tests Passed!")

if __name__ == "__main__":
    test_normalization()
