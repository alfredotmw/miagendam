import sys
import os
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

# Add current dir to path
sys.path.append(os.getcwd())

from database import engine, Base
from models.user import User
from models.agenda import Agenda
from models.user_agenda import user_agendas

def migrate():
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # 1. Create association table if not exists (using metadata)
        print("🔍 Checking if user_agendas table exists...")
        inspector = inspect(engine)
        if not inspector.has_table("user_agendas"):
            print("🚀 Creating user_agendas table...")
            user_agendas.create(engine)
        else:
            print("✅ user_agendas table already exists.")
            
        # 2. Extract legacy permissions and migrate
        print("🔍 Reading legacy permissions from 'users' table...")
        users = db.query(User).all()
        
        migrated_count = 0
        for user in users:
            if user.allowed_agendas:
                print(f"👤 Processing user: {user.username} (Legacy: {user.allowed_agendas})")
                try:
                    agenda_ids = [int(x.strip()) for x in user.allowed_agendas.split(",") if x.strip()]
                    for aid in agenda_ids:
                        # Check if agenda exists
                        agenda = db.query(Agenda).filter(Agenda.id == aid).first()
                        if agenda:
                            # 🛡️ Idempotent check
                            existing = db.execute(
                                user_agendas.select().where(
                                    user_agendas.c.user_id == user.id,
                                    user_agendas.c.agenda_id == aid
                                )
                            ).first()
                            
                            if not existing:
                                print(f"  🔗 Linking to agenda {aid}...")
                                db.execute(user_agendas.insert().values(user_id=user.id, agenda_id=aid))
                                migrated_count += 1
                            else:
                                print(f"  ⏩ Link already exists for agenda {aid}, skipping.")
                        else:
                            print(f"  ⚠️ Agenda {aid} not found, skipping.")
                except Exception as e:
                    print(f"  ❌ Error processing legacy string for {user.username}: {e}")
        
        db.commit()
        print(f"🎉 Migration completed! {migrated_count} links processed.")
        
        print("\n💡 NOTE: The 'allowed_agendas' column has NOT been deleted for safety.")
        print("💡 You can delete it manually later with: ALTER TABLE users DROP COLUMN allowed_agendas;")

    except Exception as e:
        db.rollback()
        print(f"🛑 CRITICAL ERROR DURING MIGRATION: {e}")
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    migrate()
