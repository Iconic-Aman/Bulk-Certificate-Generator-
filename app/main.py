import os
import sys
from fastapi import FastAPI

# Add directory paths to sys.path so 'app' and root imports resolve
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
for path in (current_dir, parent_dir):
    if path not in sys.path:
        sys.path.insert(0, path)

# Temporarily commented out until underlying modules (deps, models, schemas) are defined:
# from app.api.routes.certificates import router as certificates_router
# from app.api.routes.jobs import router as jobs_router

api_prefix = os.getenv("API_V1_PREFIX", "")

app = FastAPI(title="Bulk Certificate Generator")

# Uncomment when route dependencies are implemented:
# app.include_router(jobs_router, prefix=api_prefix, tags=["jobs"])
# app.include_router(certificates_router, prefix=api_prefix, tags=["certificates"])


@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok"}