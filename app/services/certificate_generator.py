import os
import tempfile
from app.services.certificate_template import generate_certificate
from app.services.storage import upload_bytes


def generate_pdf(cert, job) -> str:
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        generate_certificate(
            path=tmp_path,
            name=cert.recipient_name,
            course=job.title,
            date=job.issue_date.strftime("%d %B %Y"),
            certificate_id=cert.certificate_number,
            issuer=job.issued_by,
        )
        with open(tmp_path, "rb") as f:
            pdf_bytes = f.read()

        key = f"certificates/{job.id}/{cert.id}.pdf"
        upload_bytes(key, pdf_bytes, content_type="application/pdf")
        return key
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
