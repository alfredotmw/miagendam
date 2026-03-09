import sys
import os

from database import SessionLocal
from models.user import User, UserRole
from models.agenda import Agenda

def apply_permissions():
    db = SessionLocal()
    try:
        users = db.query(User).all()
        all_agendas = db.query(Agenda).all()
        
        updated_count = 0
        
        for user in users:
            # Clear existing just in case
            user.agendas = []
            
            if user.role in [UserRole.ADMIN, UserRole.RECEPCION]:
                # Give admins and receptionists access to all agendas
                user.agendas.extend(all_agendas)
                print(f"✅ User {user.username} ({user.role}): Assigned ALL agendas ({len(all_agendas)})")
                updated_count += 1
            elif user.role == UserRole.MEDICO:
                # Give Medico access to all agendas for now to avoid blocking them,
                # or match by name. Let's assign them all for now to be safe, 
                # as the current issue is severe (no one sees anything).
                # To be precise, let's assign them their own agendas if we can match:
                matched = [a for a in all_agendas if a.profesional and user.username.lower() in a.profesional.lower()]
                if not matched:
                    # Give them all if no match, so they aren't completely blocked
                    user.agendas.extend(all_agendas)
                    print(f"⚠️ User {user.username} ({user.role}): No exact match found, assigned ALL agendas ({len(all_agendas)})")
                else:
                    user.agendas.extend(matched)
                    print(f"✅ User {user.username} ({user.role}): Assigned {len(matched)} matching agendas")
                updated_count += 1

        db.commit()
        print(f"\n🎉 Successfully updated permissions for {updated_count} users.")
    except Exception as e:
        print(f"❌ Error applying permissions: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    apply_permissions()
