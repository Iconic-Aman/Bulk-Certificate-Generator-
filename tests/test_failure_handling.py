from app.models import Certificate


def test_individual_certificate_failure_isolation(client, db, monkeypatch):
    # Patch generator BEFORE request so background task uses it
    orig_generate = __import__("app.services.certificate_generator", fromlist=["generate_pdf"]).generate_pdf

    def faulty_generate(cert, job):
        if cert.recipient_name == "Crash Student":
            raise RuntimeError("Simulated render engine crash")
        return orig_generate(cert, job)

    monkeypatch.setattr("app.services.job_processor.generate_pdf", faulty_generate)

    payload = {
        "title": "Cloud Architecture",
        "issued_by": "Cloud Academy",
        "issue_date": "2026-10-07",
        "recipients": [
            {"name": "Good Student", "email": "good@example.com"},
            {"name": "Crash Student", "email": "crash@example.com"},
        ],
    }
    resp = client.post("/api/jobs", json=payload)
    assert resp.status_code == 202
    job_id = resp.json()["job_id"]

    # Verify database state
    certs = db.query(Certificate).filter_by(job_id=job_id).all()
    statuses = {c.recipient_name: (c.status, c.error_message) for c in certs}

    assert statuses["Good Student"][0] == "success"
    assert statuses["Crash Student"][0] == "failed"
    assert "Simulated render engine crash" in statuses["Crash Student"][1]

    # Verify status API reflects the failure
    status_resp = client.get(f"/api/jobs/{job_id}")
    assert status_resp.status_code == 200
    data = status_resp.json()
    assert data["status"] == "completed_with_errors"
    assert data["counts"]["success"] == 1
    assert data["counts"]["failed"] == 1
    assert len(data["failures"]) == 1
    assert data["failures"][0]["status"] == "failed"
