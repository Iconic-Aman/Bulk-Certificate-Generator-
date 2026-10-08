from app.services.job_processor import process_job


def test_unknown_job_returns_404(client):
    response = client.get("/api/jobs/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


def test_job_status_completed(client, monkeypatch):
    # Process job synchronously
    payload = {
        "title": "Machine Learning",
        "issued_by": "DeepTech",
        "issue_date": "2026-10-07",
        "recipients": [
            {"name": "Alice", "email": "alice@example.com"},
            {"name": "Bob", "email": "bob@example.com"},
        ],
    }
    resp = client.post("/api/jobs", json=payload)
    job_id = resp.json()["job_id"]

    # Run background processor explicitly with mock
    monkeypatch.setattr("app.database.SessionLocal", lambda: client.app.dependency_overrides[list(client.app.dependency_overrides.keys())[0]]())
    process_job(job_id)

    status_resp = client.get(f"/api/jobs/{job_id}")
    assert status_resp.status_code == 200
    data = status_resp.json()
    assert data["status"] in ("pending", "processing", "completed")
    assert data["progress"]["total"] == 2
    assert "counts" in data


def test_job_status_completed_with_errors(client):
    payload = {
        "title": "Data Science",
        "issued_by": "Academy",
        "issue_date": "2026-10-07",
        "recipients": [
            {"name": "Valid Student", "email": "valid@example.com"},
            {"name": "", "email": "bad@example.com"},  # invalid
        ],
    }
    resp = client.post("/api/jobs", json=payload)
    job_id = resp.json()["job_id"]

    status_resp = client.get(f"/api/jobs/{job_id}")
    assert status_resp.status_code == 200
    data = status_resp.json()
    assert data["counts"].get("invalid") == 1
    assert len(data["failures"]) == 1
    assert data["failures"][0]["position"] == 1
