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


def save_job_and_rows(db, payload):
    if len(payload.recipients) > MAX_RECIPIENTS:
        raise HTTPException(status_code=413, detail=f"Max {MAX_RECIPIENTS} recipients allowed")

    job = Job(
        id=str(uuid.uuid4()),
        title=payload.title,
        issued_by=payload.issued_by,
        status="pending",
        total_count=len(payload.recipients),
    )
    db.add(job)
    db.flush()

    seen, accepted, rejected_items = set(), 0, []
    for i, r in enumerate(payload.recipients):
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
    db.commit()
    return {"job_id": job.id, "status": "pending", "total": len(payload.recipients),
            "accepted": accepted, "rejected": len(rejected_items), "rejected_items": rejected_items}


def get_job_status(db, job_id):
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    counts = dict(db.execute(
        db.query(Certificate.status, func.count(Certificate.id))
        .filter(Certificate.job_id == job_id).group_by(Certificate.status).statement
    ).fetchall())
    processed = sum(v for k, v in counts.items() if k != "pending")
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
    import io, zipfile
    from app.services.storage import get_bytes, get_presigned_url, upload_bytes

    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    certs = db.query(Certificate).filter_by(job_id=job_id, status="success").all()
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for c in certs:
            if c.file_path:
                pdf_data = get_bytes(c.file_path)
                zf.writestr(f"{c.recipient_name}_{c.id}.pdf", pdf_data)
    buf.seek(0)
    zip_key = f"zips/{job_id}.zip"
    upload_bytes(zip_key, buf.getvalue(), content_type="application/zip")
    return get_presigned_url(zip_key, filename=f"job_{job_id}.zip")
