import os

SECRET_KEY = "supersecreto123"  # después ponelo en variable de entorno
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
ENABLE_CLINICAL_REPORTS = os.getenv("ENABLE_CLINICAL_REPORTS", "true").lower() == "true"
