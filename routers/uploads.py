import shutil
import os
import uuid
from pathlib import Path
from fastapi import APIRouter, File, UploadFile, HTTPException

router = APIRouter(prefix="/uploads", tags=["Uploads"])

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}

@router.post("/image")
async def upload_image(file: UploadFile = File(...)):
    # 1. Validate Extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Tipo de archivo no permitido. Solo imágenes.")

    # 2. Generate Unique Filename
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = UPLOAD_DIR / unique_filename

    # 3. Save File
    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al guardar imagen: {e}")
    
    # 4. Return URL
    # Assuming the app mounts /static/uploads or similar. 
    # Let's verify how main.py mounts statics.
    # If we mount UPLOAD_DIR at /uploads_static
    return {"url": f"/uploads_static/{unique_filename}", "filename": unique_filename}
