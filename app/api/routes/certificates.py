from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from app.api.deps import get_db, verify_api_key
from app.models import Certificate

router = APIRouter(dependencies=[Depends(verify_api_key)])


@router.get("/certificates/{cert_id}/download")
def download_certificate(cert_id: str, db=Depends(get_db)):
    cert = db.get(Certificate, cert_id)
    if not cert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Certificate not found")
    if cert.status != "success" or not cert.file_path:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Certificate cannot be downloaded: status is {cert.status}",
        )
    return FileResponse(cert.file_path, filename=f"cert_{cert.id}.pdf", media_type="application/pdf")
