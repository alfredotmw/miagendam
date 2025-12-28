from database import engine, Base
import models.radioterapia # Ensure model is imported

def create_table():
    print("Creating tables for Radiotherapy...")
    Base.metadata.create_all(bind=engine)
    print("Done.")

if __name__ == "__main__":
    create_table()
