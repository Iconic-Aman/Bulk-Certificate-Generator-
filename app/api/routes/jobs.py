import os
from fastapi import APIRouter, BackgroundTasks, Depends
from fastapi.responses import FileResponse
from app.api.deps import get_db
from app.schemas.job import JobCreate
from app.services.job_processor import process_job
from app.services.job_service import get_job_status, get_job_zip, save_job_and_rows

router = APIRouter()


@router.post("/jobs", status_code=202)
def create_job(payload: JobCreate, background_tasks: BackgroundTasks, db=Depends(get_db)):
    response = save_job_and_rows(db, payload)
    background_tasks.add_task(process_job, response["job_id"])
    status_url_base = os.getenv("JOB_STATUS_URL_BASE", "")
    response["status_url"] = f"{status_url_base}/{response['job_id']}"
    return response


@router.get("/jobs/{job_id}")
def get_job(job_id: str, db=Depends(get_db)):
    return get_job_status(db, job_id)


@router.get("/jobs/{job_id}/download")
def download_job_zip(job_id: str, db=Depends(get_db)):
    zip_path = get_job_zip(db, job_id)
    return FileResponse(zip_path, filename=f"job_{job_id}.zip", media_type="application/zip")
