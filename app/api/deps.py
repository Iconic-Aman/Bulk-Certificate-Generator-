import os
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from app.database import get_db  # noqa: F401

_api_key_header = APIKeyHeader(name="X-API-Key")


def verify_api_key(key: str = Security(_api_key_header)):
    if key != os.getenv("API_KEY"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid API key")
