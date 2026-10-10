from datetime import date
import os
import tempfile
from app.services.certificate_template import generate_certificate
from app.services.storage import upload_bytes


def generate_and_upload(job_id: str, cert_id: str, name: str, title: str, issued_by: str, issue_date, cert_number: str) -> str:
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        cert_date = issue_date or date.today()
        date_str = cert_date.strftime("%d %B %Y") if hasattr(cert_date, "strftime") else str(cert_date)
        generate_certificate(
            path=tmp_path,
            name=name,
            course=title,
            date=date_str,
            certificate_id=cert_number,
            issuer=issued_by,
        )
        with open(tmp_path, "rb") as f:
            pdf_bytes = f.read()

        key = f"certificates/{job_id}/{cert_id}.pdf"
        upload_bytes(key, pdf_bytes, content_type="application/pdf")
        return key
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def generate_pdf(cert, job) -> str:
    return generate_and_upload(
        job_id=str(job.id),
        cert_id=str(cert.id),
        name=cert.recipient_name,
        title=job.title,
        issued_by=job.issued_by,
        issue_date=cert.issue_date,
        cert_number=cert.certificate_number,
    )
