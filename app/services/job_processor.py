import logging
from datetime import datetime, timezone
from app.database import SessionLocal
from app.models import Certificate, Job
from app.services.certificate_generator import generate_pdf

logger = logging.getLogger("job_processor")


def process_job(job_id):
    logger.info("Processing job: %s", job_id)
    db = SessionLocal()
    try:
        job = db.get(Job, job_id)
        if not job:
            logger.error("Job %s not found in DB", job_id)
            return

        job.status = "processing"
        job.started_at = datetime.now(timezone.utc)
        db.commit()

        certs = db.query(Certificate).filter_by(job_id=job_id, status="pending").all()
        logger.info("Job %s: %d pending certificates to generate", job_id, len(certs))

        for i, cert in enumerate(certs, 1):
            logger.info("Job %s [%d/%d]: Generating for '%s' (%s)", job_id, i, len(certs), cert.recipient_name, cert.id)
            try:
                cert.file_path = generate_pdf(cert, job)
                cert.status = "success"
                logger.info("Job %s [%d/%d]: SUCCESS -> %s", job_id, i, len(certs), cert.file_path)
            except Exception as e:
                cert.status = "failed"
                cert.error_message = str(e)
                logger.error("Job %s [%d/%d]: FAILED -> %s", job_id, i, len(certs), e, exc_info=True)
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
        logger.info("Job %s FINISHED -> final status: %s (success: %d, failed/invalid: %d)", job_id, job.status, success, failed_or_invalid)
    finally:
        db.close()