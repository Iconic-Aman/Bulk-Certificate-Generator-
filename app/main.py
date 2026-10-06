import os
from fastapi import FastAPI
from app.api.routes.certificates import router as certificates_router
from app.api.routes.jobs import router as jobs_router

api_prefix = os.getenv("API_V1_PREFIX", "")

app = FastAPI(title="Bulk Certificate Generator")

app.include_router(jobs_router, prefix=api_prefix, tags=["jobs"])
app.include_router(certificates_router, prefix=api_prefix, tags=["certificates"])


@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok"}