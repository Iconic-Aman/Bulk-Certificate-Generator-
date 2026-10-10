import re
import uuid
from fastapi import HTTPException
from sqlalchemy import func
from app.models import Certificate, Job

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MAX_RECIPIENTS = 1000


def _validate_recipient(name, email, seen):
    name = name.strip()
    email = email.strip().lower()
    if not name or len(name) > 100:
        return name, email, "recipient_name: must be 1–100 characters"
    if not EMAIL_RE.match(email):
        return name, email, "recipient_email: not a valid email address"
    if email in seen:
        return name, email, "recipient_email: duplicate email in job"
    return name, email, None


from datetime import date
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError


def save_job_and_rows(db, payload):
    if len(payload.recipients) > MAX_RECIPIENTS:
        raise HTTPException(status_code=413, detail=f"Max {MAX_RECIPIENTS} recipients allowed")

    incoming_emails = [r.email.strip().lower() for r in payload.recipients if r.email]
    already = set(
        db.scalars(
            select(Certificate.recipient_email).where(
                Certificate.title == payload.title,
                Certificate.recipient_email.in_(incoming_emails),
                Certificate.status != "invalid",
            )
        ).all()
    ) if incoming_emails else set()

    new_recipients = [r for r in payload.recipients if r.email.strip().lower() not in already]
    skipped = [r.email.strip().lower() for r in payload.recipients if r.email.strip().lower() in already]

    if not new_recipients:
        return {
            "job_id": None,
            "status": "skipped",
            "message": "All recipients already have certificates for this title",
            "total": len(payload.recipients),
            "accepted": 0,
            "rejected": 0,
            "skipped": skipped,
            "rejected_items": [],
        }

    job = Job(
        id=str(uuid.uuid4()),
        title=payload.title,
        issued_by=payload.issued_by,
        status="pending",
        total_count=len(new_recipients),
    )
    db.add(job)
    db.flush()

    seen, accepted, rejected_items = set(), 0, []
    for i, r in enumerate(new_recipients):
        name, email, err = _validate_recipient(r.name, r.email, seen)
        cert_date = getattr(r, "issue_date", None) or date.today()
        if err:
            rejected_items.append({"position": i, "error": err})
            db.add(Certificate(id=str(uuid.uuid4()), job_id=job.id, position=i,
                               recipient_name=name or r.name, recipient_email=email or r.email,
                               title=job.title,
                               issue_date=cert_date,
                               status="invalid", error_message=err))
        else:
            seen.add(email)
            accepted += 1
            db.add(Certificate(id=str(uuid.uuid4()), job_id=job.id, position=i,
                               recipient_name=name, recipient_email=email,
                               title=job.title,
                               issue_date=cert_date,
                               certificate_number=f"CERT-{cert_date.year}-{uuid.uuid4().hex[:6].upper()}",
                               status="pending"))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Duplicate certificate submission in progress")

    return {"job_id": job.id, "status": "pending", "total": len(payload.recipients),
            "accepted": accepted, "rejected": len(rejected_items), "skipped": skipped,
            "rejected_items": rejected_items}


import logging

logger = logging.getLogger("jobs")


def get_job_status(db, job_id):
    logger.info("Fetching status for job_id: %s", job_id)
    try:
        uuid.UUID(str(job_id))
    except (ValueError, AttributeError):
        logger.warning("Invalid UUID format for job_id: %s", job_id)
        raise HTTPException(status_code=404, detail="Job not found")

    try:
        job = db.get(Job, job_id)
    except Exception as e:
        logger.error("DB error fetching job %s: %s", job_id, e, exc_info=True)
        raise HTTPException(status_code=500, detail="Database query error")

    if not job:
        logger.info("Job not found in db: %s", job_id)
        raise HTTPException(status_code=404, detail="Job not found")
    counts = dict(db.execute(
        db.query(Certificate.status, func.count(Certificate.id))
        .filter(Certificate.job_id == job_id).group_by(Certificate.status).statement
    ).fetchall())
    processed = sum(counts.get(k, 0) for k in ("success", "failed", "invalid"))
    total = job.total_count or 1
    failed_certs = db.query(Certificate).filter(
        Certificate.job_id == job_id,
        Certificate.status.in_(("failed", "invalid")),
    ).all()
    failures = [
        {"certificate_id": c.id, "position": c.position, "status": c.status, "error": c.error_message}
        for c in failed_certs
    ]

    return {"job_id": job.id, "title": job.title, "status": job.status,
            "progress": {"total": job.total_count, "processed": processed,
                         "percent": round(processed / total * 100)},
            "counts": counts, "failures": failures,
            "created_at": job.created_at, "started_at": job.started_at, "finished_at": job.finished_at}


def get_job_zip(db, job_id):
    import io, re, zipfile
    from concurrent.futures import ThreadPoolExecutor
    from app.services.storage import get_bytes, get_presigned_url, upload_bytes

    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    certs = [c for c in db.query(Certificate).filter_by(job_id=job_id, status="success").all() if c.file_path]
    with ThreadPoolExecutor(max_workers=10) as pool:
        pdfs = list(pool.map(get_bytes, [c.file_path for c in certs]))

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for c, data in zip(certs, pdfs):
            safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "_", c.recipient_name)
            zf.writestr(f"{safe_name}_{c.id}.pdf", data)

    buf.seek(0)
    zip_key = f"zips/{job_id}.zip"
    upload_bytes(zip_key, buf.getvalue(), content_type="application/zip")
    return get_presigned_url(zip_key, filename=f"job_{job_id}.zip")
