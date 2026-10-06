from datetime import date
from typing import List
from pydantic import BaseModel


class RecipientIn(BaseModel):
    name: str = ""
    email: str = ""


class JobCreate(BaseModel):
    title: str
    issued_by: str
    issue_date: date
    recipients: List[RecipientIn]
