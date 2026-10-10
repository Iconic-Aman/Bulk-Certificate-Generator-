import json
import os
from datetime import date
from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from app.api.deps import get_db, verify_api_key
from app.schemas.job import JobCreate
from app.services.job_processor import process_job
from app.services.job_service import get_job_status, get_job_zip, save_job_and_rows

router = APIRouter(dependencies=[Depends(verify_api_key)])


@router.post("/jobs", status_code=202)
def create_job(payload: JobCreate, background_tasks: BackgroundTasks, db=Depends(get_db)):
    response = save_job_and_rows(db, payload)
    if response.get("job_id"):
        background_tasks.add_task(process_job, response["job_id"])
        status_url_base = os.getenv("JOB_STATUS_URL_BASE", "")
        response["status_url"] = f"{status_url_base}/{response['job_id']}"
    return response


@router.post("/jobs/upload", status_code=202)
async def upload_job_json(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: str = "Certificate of Completion",
    issued_by: str = "Acme Academy",
    db=Depends(get_db),
):
    try:
        content = await file.read()
        raw = json.loads(content.decode("utf-8"))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON file: {e}")

    recipients = raw if isinstance(raw, list) else raw.get("recipients", [])
    if isinstance(raw, dict):
        title = raw.get("title", title)
        issued_by = raw.get("issued_by", issued_by)
        default_date = raw.get("issue_date")
        if default_date:
            for r in recipients:
                if isinstance(r, dict) and "issue_date" not in r:
                    r["issue_date"] = default_date

    payload = JobCreate(
        title=title,
        issued_by=issued_by,
        recipients=recipients,
    )
    return create_job(payload, background_tasks, db)


import logging

logger = logging.getLogger("jobs")


@router.get("/jobs/{job_id}")
def get_job(job_id: str, db=Depends(get_db)):
    logger.info("GET /jobs/%s requested", job_id)
    return get_job_status(db, job_id)


@router.get("/jobs/{job_id}/download")
def download_job_zip(job_id: str, db=Depends(get_db)):
    download_url = get_job_zip(db, job_id)
    return {
        "job_id": job_id,
        "download_url": download_url,
    }
