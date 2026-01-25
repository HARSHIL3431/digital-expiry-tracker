import shutil
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException

from app.services.scan_service import ScanService
from app.schemas.scan import ScanResponse

router = APIRouter(prefix="/scan", tags=["OCR"])

scanner = ScanService()

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@router.post("/image", response_model=ScanResponse)
def scan_image(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Invalid file type")

    file_path = UPLOAD_DIR / file.filename

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    result = scanner.scan_image(str(file_path))

    return result
