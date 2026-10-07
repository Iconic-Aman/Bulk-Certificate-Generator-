import os
from pathlib import Path
from app.services.certificate_template import generate_certificate

STORAGE_DIR = Path(os.getenv("STORAGE_DIR", "storage"))


def generate_pdf(cert, job) -> str:
    out_dir = STORAGE_DIR / str(job.id)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{cert.id}.pdf"
    generate_certificate(
        path=path,
        name=cert.recipient_name,
        course=job.title,
        date=job.issue_date.strftime("%d %B %Y"),
        certificate_id=cert.certificate_number,
        issuer=job.issued_by,
    )
    return str(path)
