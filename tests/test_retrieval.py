from datetime import date
from app.models import Certificate, Job


def test_download_success_certificate(client, db):
    job = Job(id="job-1", title="Python", issued_by="Acme")
    cert = Certificate(
        id="cert-1",
        job_id="job-1",
        position=0,
        recipient_name="Sam",
        recipient_email="sam@example.com",
        title=job.title,
        status="success",
        issue_date=date(2026, 10, 7),
        file_path="certificates/job-1/cert-1.pdf",
    )
    db.add(job)
    db.add(cert)
    db.commit()

    resp = client.get("/api/certificates/cert-1/download")
    assert resp.status_code == 200
    data = resp.json()
    assert "download_url" in data
    assert "certificates/job-1/cert-1.pdf" in data["download_url"]


def test_download_unknown_certificate_returns_404(client):
    resp = client.get("/api/certificates/non-existent-id/download")
    assert resp.status_code == 404


def test_download_unsuccessful_certificate_returns_409(client, db):
    job = Job(id="job-2", title="Python", issued_by="Acme")
    cert = Certificate(
        id="cert-failed",
        job_id="job-2",
        position=0,
        recipient_name="Failed Student",
        recipient_email="fail@example.com",
        title=job.title,
        status="failed",
        issue_date=date(2026, 10, 7),
    )
    db.add(job)
    db.add(cert)
    db.commit()

    resp = client.get("/api/certificates/cert-failed/download")
    assert resp.status_code == 409


def test_download_without_auth_returns_401_or_403(client):
    from fastapi.testclient import TestClient
    c = TestClient(client.app)
    resp = c.get("/api/certificates/any-id/download")
    assert resp.status_code in (401, 403)


def test_download_job_zip(client, db):
    job = Job(id="job-zip", title="Python", issued_by="Acme")
    cert = Certificate(
        id="cert-zip-1",
        job_id="job-zip",
        position=0,
        recipient_name="Sam",
        recipient_email="sam@example.com",
        title=job.title,
        status="success",
        issue_date=date(2026, 10, 7),
        file_path="certificates/job-zip/cert-zip-1.pdf",
    )
    db.add(job)
    db.add(cert)
    db.commit()

    resp = client.get("/api/jobs/job-zip/download")
    assert resp.status_code == 200
    data = resp.json()
    assert "download_url" in data
    assert "zips/job-zip.zip" in data["download_url"]
