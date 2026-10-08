# Bulk Certificate Generator

Asynchronous REST API to generate and deliver PDF certificates in bulk using FastAPI, ReportLab, Supabase PostgreSQL, and Cloudflare R2 storage.

---

## 1. Features
- **Asynchronous Execution:** Non-blocking bulk submissions return `202 Accepted` immediately.
- **Fault-Tolerant Processing:** Per-certificate isolation; a failure in one certificate never halts the remaining batch.
- **Cloud Storage:** Certificates and ZIP bundles are stored in Cloudflare R2 and served via presigned URLs.
- **Two-Tier Validation:** Request-level validation rejects malformed requests, while recipient-level validation isolates bad records.
- **Live Progress Tracking:** Job status queries compute live counts dynamically without counter drift.

---

## 2. Environment Variables

Create a `.env` file in the root directory:

```env
DATABASE_URL=postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres
API_PREFIX=/api
JOB_STATUS_URL_BASE=/api/jobs
STORAGE_DIR=storage
API_KEY=your-secret-api-key

# Cloudflare R2 Credentials
R2_ENDPOINT=https://<ACCOUNT_ID>.r2.cloudflarestorage.com
R2_ACCESS_KEY=<R2_ACCESS_KEY_ID>
R2_SECRET_KEY=<R2_SECRET_ACCESS_KEY>
R2_BUCKET=certificates
```

---

## 3. Setup & Installation

### Local Setup (using `uv`)
```bash
git clone <repo-url>
cd Bulk-Certificate-Generator-
cd app
uv sync
```

### Database Migration
Execute `schema.sql` in your PostgreSQL / Supabase SQL editor to create the `jobs` and `certificates` tables and indexes.

---

## 4. Running the Application

### Local Development
```bash
cd app
uv run uvicorn main:app --reload --port 8000
```
Swagger UI will be available at: `http://localhost:8000/api/docs`

### Render Deployment
- **Build Command:** `cd app && pip install .`
- **Start Command:** `cd app && uvicorn main:app --host 0.0.0.0 --port $PORT`
- **Environment:** Add all `.env` variables in Render Dashboard.

---

## 5. Running Tests

Run the full pytest test suite (16 tests across 6 modules using SQLite in-memory DB and mocked R2):

```bash
uv run pytest tests -v
```

Test coverage includes:
- `test_create_job.py`: Job creation, 202 status, DB rows.
- `test_validation.py`: 422 schemas, 413 recipient limit, malformed and duplicate emails.
- `test_generator.py`: PDF binary structure, unicode names, and auto-scaling long text.
- `test_job_status.py`: Metrics calculation, status transitions, 404 handling.
- `test_failure_handling.py`: Generator crash isolation, error reporting.
- `test_retrieval.py`: Presigned single PDF and ZIP download links, 401/403/409 handling.

---

## 6. API Usage

All protected routes require the `X-API-Key` header.

### 1. Submit Generation Job
```bash
curl -X POST "http://localhost:8000/api/jobs" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-secret-api-key" \
  -d '{
    "title": "Cloud Computing Specialization",
    "issued_by": "Acme Academy",
    "issue_date": "2026-10-09",
    "recipients": [
      {"name": "Alice Smith", "email": "alice@example.com"},
      {"name": "Bob Jones", "email": "bob@example.com"}
    ]
  }'
```
**Response (202 Accepted):**
```json
{
  "job_id": "c1f7b7f1-...",
  "status": "pending",
  "total": 2,
  "accepted": 2,
  "rejected": 0,
  "rejected_items": [],
  "status_url": "/api/jobs/c1f7b7f1-..."
}
```

### 2. Check Job Status & Progress
```bash
curl -X GET "http://localhost:8000/api/jobs/{job_id}" \
  -H "X-API-Key: your-secret-api-key"
```
**Response (200 OK):**
```json
{
  "job_id": "c1f7b7f1-...",
  "status": "completed",
  "progress": {"total": 2, "processed": 2, "percent": 100},
  "counts": {"success": 2},
  "failures": []
}
```

### 3. Retrieve Single Certificate
```bash
curl -X GET "http://localhost:8000/api/certificates/{cert_id}/download" \
  -H "X-API-Key: your-secret-api-key"
```
**Response (200 OK):** Returns a JSON object containing a 1-hour presigned Cloudflare R2 download URL:
```json
{
  "certificate_id": "{cert_id}",
  "recipient_name": "Alice Smith",
  "download_url": "https://<account>.r2.cloudflarestorage.com/certificates/..."
}
```

### 4. Retrieve All Certificates as ZIP
```bash
curl -X GET "http://localhost:8000/api/jobs/{job_id}/download" \
  -H "X-API-Key: your-secret-api-key"
```
**Response (200 OK):** Returns a presigned Cloudflare R2 download link for the bundled archive (`zips/{job_id}.zip`).

---

## 7. Key Architecture & Design Decisions

1. **FastAPI Background Tasks:**
   Decouples PDF rendering from the HTTP request loop, avoiding gateway timeouts on bulk submissions.
2. **Cloudflare R2 Direct Offloading:**
   FastAPI generates presigned URLs rather than proxying heavy binary payloads through the web server.
3. **Database-backed Progress Queries:**
   Job counts are evaluated dynamically with `GROUP BY` rather than relying on cached counters that could drift on crash.
4. **Per-Certificate Exception Guard:**
   Each certificate generation is wrapped in a dedicated `try/except` and committed immediately, ensuring one failure never halts the entire batch.
