import os
import sys
from dotenv import load_dotenv
from fastapi import FastAPI

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
for path in (current_dir, parent_dir):
    if path not in sys.path:
        sys.path.insert(0, path)

load_dotenv(os.path.join(parent_dir, ".env"))
load_dotenv(os.path.join(current_dir, ".env"))

from app.api.routes.certificates import router as certificates_router
from app.api.routes.jobs import router as jobs_router

api_prefix = os.getenv("API_PREFIX", "/api")

app = FastAPI(
    title="Bulk Certificate Generator",
    docs_url=f"{api_prefix}/docs",
    redoc_url=f"{api_prefix}/redoc",
    openapi_url=f"{api_prefix}/openapi.json",
)

app.include_router(jobs_router, prefix=api_prefix, tags=["jobs"])
app.include_router(certificates_router, prefix=api_prefix, tags=["certificates"])


@app.get(f"{api_prefix}/health", tags=["health"])
def health_check():
    return {"status": "ok"}