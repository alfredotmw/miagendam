
from database import SessionLocal
from routers.analytics import get_live_data
import pandas as pd

db = SessionLocal()
print("Fetching live data...")
data = get_live_data(db)
print(f"Rows fetched: {len(data)}")

df = pd.DataFrame(data)
file_path = "reporte_agendas.xlsx"
df.to_excel(file_path, index=False)
print(f"Excel file regenerated at: {file_path}")

db.close()
