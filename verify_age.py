from datetime import date
from models.paciente import Paciente

def test_age_calc():
    try:
        # 1. Test Patient with DOB
        dob = date(1990, 1, 1)
        p = Paciente(nombre="Test", apellido="Age", dni="TEST_AGE", fecha_nacimiento=dob)
        print(f"DOB: {dob}")
        print(f"Calculated Age: {p.edad}")

        # Basic math check
        today = date.today()
        expected = today.year - 1990 - ((today.month, today.day) < (1, 1))
        
        if p.edad == expected:
            print("VERIFICATION SUCCESS: Age matched expected value.")
        else:
            print(f"VERIFICATION FAILED: Expected {expected}, got {p.edad}")

    except Exception as e:
        print(f"Verification ERROR: {e}")

if __name__ == "__main__":
    test_age_calc()
