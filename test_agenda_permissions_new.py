import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add current dir to path
sys.path.append(os.getcwd())

from database import engine, Base
from models.user import User, UserRole
from models.agenda import Agenda
from models.user_agenda import user_agendas
from routers.agendas import listar_agendas

# Mock current_user for Depends
def mock_current_user(username, role):
    return {"username": username, "role": role}

def test_permissions():
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        print("🧪 Starting Permission Tests...")
        
        # 1. Cleanup/Setup Test Data
        print("🧹 Cleaning up old test data...")
        db.execute(user_agendas.delete()) # Clear association table first
        db.query(User).filter(User.username.like("test_perm_%")).delete(synchronize_session=False)
        db.query(Agenda).filter(Agenda.nombre.like("TEST_AGENDA_%")).delete(synchronize_session=False)
        db.commit()
        
        # Create Users
        admin = User(username="test_perm_admin", password="pw", role="ADMIN")
        user1 = User(username="test_perm_user1", password="pw", role="RECEPCION")
        user2 = User(username="test_perm_user2", password="pw", role="RECEPCION")
        db.add_all([admin, user1, user2])
        db.commit()
        
        # Create Agendas
        a1 = Agenda(nombre="TEST_AGENDA_1", tipo="MEDICO", activo=True)
        a2 = Agenda(nombre="TEST_AGENDA_2", tipo="MEDICO", activo=True)
        a3 = Agenda(nombre="TEST_AGENDA_3", tipo="MEDICO", activo=True)
        db.add_all([a1, a2, a3])
        db.commit()
        
        # 2. Assign Permissions
        # User 1 -> Agenda 1
        # User 2 -> Agenda 2
        # Agenda 3 -> No one (except Admin)
        print("🔗 Assigning permissions...")
        user1.agendas.append(a1)
        user2.agendas.append(a2)
        db.commit()
        
        # 3. Test Listing Logic
        
        # ADMIN TEST
        print("🛡️ Testing ADMIN bypass...")
        agendas_admin = listar_agendas(db, mock_current_user("test_perm_admin", "ADMIN"))
        assert len(agendas_admin) >= 3, f"Admin should see at least 3 agendas, saw {len(agendas_admin)}"
        print("✅ Admin bypass OK.")

        # USER 1 TEST
        print("👤 Testing USER 1 (Specific access)...")
        agendas_u1 = listar_agendas(db, mock_current_user("test_perm_user1", "RECEPCION"))
        names_u1 = [a.nombre for a in agendas_u1]
        assert "TEST_AGENDA_1" in names_u1, "User 1 should see Agenda 1"
        assert "TEST_AGENDA_2" not in names_u1, "User 1 should NOT see Agenda 2"
        assert "TEST_AGENDA_3" not in names_u1, "User 1 should NOT see Agenda 3"
        print("✅ User 1 permissions OK.")

        # USER 2 TEST
        print("👤 Testing USER 2 (Specific access)...")
        agendas_u2 = listar_agendas(db, mock_current_user("test_perm_user2", "RECEPCION"))
        names_u2 = [a.nombre for a in agendas_u2]
        assert "TEST_AGENDA_2" in names_u2, "User 2 should see Agenda 2"
        assert "TEST_AGENDA_1" not in names_u2, "User 2 should NOT see Agenda 1"
        print("✅ User 2 permissions OK.")

        print("\n🏆 ALL PERMISSION TESTS PASSED!")

    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        # Cleanup
        db.query(User).filter(User.username.like("test_perm_%")).delete(synchronize_session=False)
        db.query(Agenda).filter(Agenda.nombre.like("TEST_AGENDA_%")).delete(synchronize_session=False)
        db.commit()
        db.close()

if __name__ == "__main__":
    test_permissions()
