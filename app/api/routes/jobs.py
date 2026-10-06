import os
import re
import uuid
from datetime import date
from typing import List

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

router = APIRouter()
app = router  # Alias so both `router` and `app` work seamlessly

MAX_RECIPIENTS_PER_JOB = 1000
EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class RecipientIn(BaseModel):
    name: str = ""
    email: str = ""


class JobCreate(BaseModel):
    title: str = Field(..., min_length=1, description="Certificate title")
    issued_by: str = Field(..., min_length=1, description="Organization / issuer name")
    issue_date: date = Field(..., description="Date of certificate issuance")
    recipients: List[RecipientIn] = Field(
        ...,
        min_length=1,
        description="List of recipients (max 1000)",
    )


class RejectedItem(BaseModel):
    position: int
    error: str


class JobCreatedResponse(BaseModel):
    job_id: str
    status: str
    total: int
    accepted: int
    rejected: int
    rejected_items: List[RejectedItem]
    status_url: str


@router.post(
    "/jobs",
    response_model=JobCreatedResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit bulk certificate generation job",
)
async def create_job(payload: JobCreate):
    # Request-level limit check
    if len(payload.recipients) > MAX_RECIPIENTS_PER_JOB:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Exceeded maximum recipient limit of {MAX_RECIPIENTS_PER_JOB}.",
        )

    seen_emails = set()
    accepted_recipients = []
    rejected_items = []

    # Recipient-level validation (does not fail the whole request)
    for index, recipient in enumerate(payload.recipients):
        name = recipient.name.strip()
        email = recipient.email.strip().lower()

        # Check name
        if not name:
            rejected_items.append(
                RejectedItem(position=index, error="recipient_name: must not be empty")
            )
            continue
        if len(name) > 100:
            rejected_items.append(
                RejectedItem(position=index, error="recipient_name: length must be between 1 and 100 characters")
            )
            continue
        if any(ord(char) < 32 for char in name):
            rejected_items.append(
                RejectedItem(position=index, error="recipient_name: control characters not allowed")
            )
            continue

        # Check email
        if not email or not EMAIL_REGEX.match(email):
            rejected_items.append(
                RejectedItem(position=index, error="recipient_email: not a valid email address")
            )
            continue

        # Check duplicates within the batch
        if email in seen_emails:
            rejected_items.append(
                RejectedItem(position=index, error="recipient_email: duplicate email in job")
            )
            continue

        seen_emails.add(email)
        accepted_recipients.append(
            {"position": index, "name": name, "email": email}
        )

    job_id = str(uuid.uuid4())
    total_count = len(payload.recipients)
    accepted_count = len(accepted_recipients)
    rejected_count = len(rejected_items)

    status_url_base = os.getenv("JOB_STATUS_URL_BASE", "")
    status_url = f"{status_url_base}/{job_id}"

    return JobCreatedResponse(
        job_id=job_id,
        status="pending",
        total=total_count,
        accepted=accepted_count,
        rejected=rejected_count,
        rejected_items=rejected_items,
        status_url=status_url,
    )
