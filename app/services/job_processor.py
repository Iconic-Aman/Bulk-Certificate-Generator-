from datetime import datetime, timezone
from app.database import SessionLocal
from app.models import Certificate, Job
from app.services.certificate_generator import generate_pdf


def process_job(job_id):
    db = SessionLocal()
    try:
        job = db.get(Job, job_id)
        if not job:
            return

        job.status = "processing"
        job.started_at = datetime.now(timezone.utc)
        db.commit()

        certs = db.query(Certificate).filter_by(job_id=job_id, status="pending").all()
        for cert in certs:
            try:
                cert.file_path = generate_pdf(cert)
                cert.status = "success"
            except Exception as e:
                cert.status = "failed"
                cert.error_message = str(e)
            db.commit()

        all_certs = db.query(Certificate).filter_by(job_id=job_id).all()
        success = sum(1 for c in all_certs if c.status == "success")
        failed_or_invalid = sum(1 for c in all_certs if c.status in ("failed", "invalid"))

        if success == 0:
            job.status = "failed"
        elif failed_or_invalid == 0:
            job.status = "completed"
        else:
            job.status = "completed_with_errors"

        job.finished_at = datetime.now(timezone.utc)
        db.commit()
    finally:
        db.close()