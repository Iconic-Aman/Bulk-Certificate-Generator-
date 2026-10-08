from datetime import date
from typing import List
from pydantic import BaseModel, Field


class RecipientIn(BaseModel):
    name: str = ""
    email: str = ""


class JobCreate(BaseModel):
    title: str = Field(..., min_length=1)
    issued_by: str = Field(..., min_length=1)
    issue_date: date
    recipients: List[RecipientIn] = Field(..., min_length=1)
