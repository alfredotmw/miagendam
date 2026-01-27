import sys
import os
sys.path.append(os.getcwd())

from routers.analytics import normalize_service

def test_normalization():
    print("Testing normalize_service...")
    
    # Test case 1: Standard Tomography
    res_tom = normalize_service("AGENDA TOMOGRAFIA", ["TOMOGRAFIA CEREBRO"])
    print(f"Test 1 (Standard): {res_tom}")
    assert res_tom == "TOMOGRAFIA", f"Expected TOMOGRAFIA, got {res_tom}"
    
    # Test case 2: TAC
    res_tac = normalize_service("AGENDA TAC", ["TAC ABDOMEN"])
    print(f"Test 2 (TAC): {res_tac}")
    assert res_tac == "TOMOGRAFIA", f"Expected TOMOGRAFIA, got {res_tac}"

    # Test case 3: TAC DE MARCACIÓN (The one we want to separate)
    res_marcacion = normalize_service("AGENDA TOMOGRAFIA", ["TAC DE MARCACIÓN"])
    print(f"Test 3 (Marcacion): {res_marcacion}")
    assert res_marcacion == "TAC DE MARCACIÓN", f"Expected TAC DE MARCACIÓN, got {res_marcacion}"
    
    # Test case 4: Mixed
    res_mix = normalize_service("AGENDA", ["CONSULTA", "TAC DE MARCACIÓN"])
    print(f"Test 4 (Mixed): {res_mix}")
    assert res_mix == "TAC DE MARCACIÓN", f"Expected TAC DE MARCACIÓN, got {res_mix}"

    print("\nALL TESTS PASSED ✅")

if __name__ == "__main__":
    try:
        test_normalization()
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
