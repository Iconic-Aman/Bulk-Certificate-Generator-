from datetime import date
from typing import List, Optional
from pydantic import BaseModel, Field


class RecipientIn(BaseModel):
    name: str = ""
    email: str = ""
    issue_date: Optional[date] = None


class JobCreate(BaseModel):
    title: str = Field(..., min_length=1)
    issued_by: str = Field(..., min_length=1)
    recipients: List[RecipientIn] = Field(..., min_length=1)
