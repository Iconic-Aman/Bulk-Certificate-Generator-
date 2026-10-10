from datetime import date
from app.models import Certificate, Job


def test_create_job_success(client, db):
    payload = {
        "title": "Python Developer",
        "issued_by": "Acme Org",
        "recipients": [
            {"name": "Alice Smith", "email": "alice@example.com", "issue_date": "2026-10-07"},
            {"name": "Bob Jones", "email": "bob@example.com", "issue_date": "2026-10-08"},
        ],
    }
    response = client.post("/api/jobs", json=payload)
    assert response.status_code == 202
    data = response.json()

    assert "job_id" in data
    assert data["status"] == "pending"
    assert data["total"] == 2
    assert data["accepted"] == 2
    assert data["rejected"] == 0
    assert data["rejected_items"] == []
    assert data["status_url"] == f"/api/jobs/{data['job_id']}"

    # Verify rows in database
    job = db.get(Job, data["job_id"])
    assert job is not None
    assert job.title == "Python Developer"
    assert job.total_count == 2

    certs = db.query(Certificate).filter_by(job_id=job.id).all()
    assert len(certs) == 2
    for cert in certs:
        assert cert.status in ("pending", "processing", "success")
        assert cert.certificate_number.startswith("CERT-2026-")
    assert certs[0].issue_date == date(2026, 10, 7)
    assert certs[1].issue_date == date(2026, 10, 8)
