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
        from concurrent.futures import ThreadPoolExecutor, as_completed
        from app.services.certificate_generator import generate_and_upload
        import time

        logger.info("Job %s: %d pending certificates to generate", job_id, len(certs))
        t_total = time.perf_counter()

        by_id = {c.id: c for c in certs}
        cert_args = [
            (c.id, c.recipient_name, c.certificate_number, c.issue_date)
            for c in certs
        ]

        class _SimpleCert:
            __slots__ = ("id", "recipient_name", "certificate_number", "issue_date")
            def __init__(self, id, name, num, dt):
                self.id, self.recipient_name, self.certificate_number, self.issue_date = id, name, num, dt

        class _SimpleJob:
            __slots__ = ("id", "title", "issued_by")
            def __init__(self, id, title, issued_by):
                self.id, self.title, self.issued_by = id, title, issued_by

        simple_job = _SimpleJob(job.id, job.title, job.issued_by)

        def task(item):
            s_cert = _SimpleCert(*item)
            return generate_pdf(s_cert, simple_job)

        done = 0
        with ThreadPoolExecutor(max_workers=10) as pool:
            futures = {pool.submit(task, item): item[0] for item in cert_args}
            for fut in as_completed(futures):
                cert = by_id[futures[fut]]
                try:
                    cert.file_path = fut.result()
                    cert.status = "success"
                except Exception as e:
                    cert.status = "failed"
                    cert.error_message = str(e)[:500]
                    logger.error("Job %s: cert %s FAILED -> %s", job_id, cert.id, e)

                done += 1
                if done % 20 == 0:
                    db.commit()

        db.commit()
        elapsed = time.perf_counter() - t_total
        print(f"Total time taken for {len(certs)} certs: {elapsed:.3f}s")
        logger.info("Job %s: Total time for %d certs: %.3fs", job_id, len(certs), elapsed)

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