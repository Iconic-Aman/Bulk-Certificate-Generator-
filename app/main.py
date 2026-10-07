import logging
import os
import sys
from dotenv import load_dotenv
from fastapi import FastAPI

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

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