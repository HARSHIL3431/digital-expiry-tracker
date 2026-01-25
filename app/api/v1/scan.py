import os
import shutil
from fastapi import APIRouter, UploadFile, File, HTTPException

from app.services.scan_service import ScanService

router = APIRouter(prefix="/scan", tags=["Scan"])
scan_service = ScanService()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/image")
async def scan_image(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Invalid image file")

    file_path = os.path.join(UPLOAD_DIR, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    result = scan_service.scan_image(file_path)

    return result
