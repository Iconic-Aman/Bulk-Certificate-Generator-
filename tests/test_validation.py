def test_missing_required_field_returns_422(client):
    payload = {
        "title": "Python Bootcamp",
        # missing issued_by
        "recipients": [{"name": "Aman", "email": "aman@example.com"}],
    }
    response = client.post("/api/jobs", json=payload)
    assert response.status_code == 422


def test_empty_recipients_returns_422(client):
    payload = {
        "title": "Python Bootcamp",
        "issued_by": "Acme",
        "recipients": [],
    }
    response = client.post("/api/jobs", json=payload)
    assert response.status_code == 422


def test_over_limit_recipients_returns_413(client):
    payload = {
        "title": "Python Bootcamp",
        "issued_by": "Acme",
        "recipients": [
            {"name": f"User {i}", "email": f"user{i}@example.com"}
            for i in range(1001)
        ],
    }
    response = client.post("/api/jobs", json=payload)
    assert response.status_code == 413


def test_recipient_validation_mixed_and_duplicates(client):
    payload = {
        "title": "Python Bootcamp",
        "issued_by": "Acme",
        "recipients": [
            {"name": "Valid One", "email": "valid1@example.com"},
            {"name": "Bad Email", "email": "not-an-email"},
            {"name": "", "email": "noname@example.com"},
            {"name": "Duplicate", "email": "valid1@example.com"},
        ],
    }
    response = client.post("/api/jobs", json=payload)
    assert response.status_code == 202
    data = response.json()

    assert data["total"] == 4
    assert data["accepted"] == 1
    assert data["rejected"] == 3
    assert len(data["rejected_items"]) == 3

    errors = {item["position"]: item["error"] for item in data["rejected_items"]}
    assert "recipient_email" in errors[1]
    assert "recipient_name" in errors[2]
    assert "duplicate email" in errors[3]
