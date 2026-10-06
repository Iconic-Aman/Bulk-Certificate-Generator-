import uuid


def save_job_and_rows(db, payload):
    return {
        "job_id": str(uuid.uuid4()),
        "status": "pending",
        "total": len(payload.recipients),
        "accepted": len(payload.recipients),
        "rejected": 0,
        "rejected_items": [],
    }


def get_job_status(db, job_id):
    return {"job_id": job_id, "status": "pending"}


def get_job_zip(db, job_id):
    return ""
