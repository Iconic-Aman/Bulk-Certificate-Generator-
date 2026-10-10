# Bulk Certificate Generator

Asynchronous REST API to generate and deliver PDF certificates in bulk using FastAPI, ReportLab, Supabase PostgreSQL, and Cloudflare R2 storage.

---

## 1. Features & Architecture
- **Asynchronous Execution:** Non-blocking bulk submissions return `202 Accepted` immediately.
- **Fault-Tolerant Processing:** Per-certificate isolation; a failure in one certificate never halts the remaining batch.
- **Cloud Storage:** Certificates and ZIP bundles are stored in Cloudflare R2 and served via presigned URLs.
- **Two-Tier Validation:** Request-level validation rejects malformed requests, while recipient-level validation isolates bad records.
- **Dynamic Live Progress:** Job counts are evaluated dynamically with `GROUP BY` to prevent counter drift.

---

## 2. Environment Variables (`.env`)
```env
DATABASE_URL=postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres
API_PREFIX=/api
JOB_STATUS_URL_BASE=/api/jobs
STORAGE_DIR=storage
API_KEY=your-secret-api-key
R2_ENDPOINT=https://<ACCOUNT_ID>.r2.cloudflarestorage.com
R2_ACCESS_KEY=<R2_ACCESS_KEY_ID>
R2_SECRET_KEY=<R2_SECRET_ACCESS_KEY>
R2_BUCKET=certificates
```

---

## 3. Setup, Run & Tests
```bash
# Setup & run locally
cd app && uv sync
uv run uvicorn main:app --reload --port 8000   # Docs: http://localhost:8000/api/docs

# Run full test suite (17 tests covering validation, generation, failure isolation, retrieval, idempotency)
uv run pytest tests -v
```
**Render Deployment:** Build: `cd app && pip install .` | Start: `cd app && uvicorn main:app --host 0.0.0.0 --port $PORT`

---

## 4. API Usage (Header: `X-API-Key: <key>`)

### 1. Submit Generation Job (JSON or File Upload)
- **JSON Body:** `POST /api/jobs`
```bash
curl -X POST "http://localhost:8000/api/jobs" -H "Content-Type: application/json" -H "X-API-Key: key" -d '{
  "title": "Cloud Computing", "issued_by": "Acme",
  "recipients": [{"name": "Alice", "email": "alice@example.com", "issue_date": "2026-10-09"}]
}'
```
- **File Upload:** `POST /api/jobs/upload` (Upload `.json` file containing recipients list via multipart form).

### 2. Check Job Status & Progress
```bash
curl -X GET "http://localhost:8000/api/jobs/{job_id}" -H "X-API-Key: key"
# Returns 200 OK with progress percent, counts (success, failed, invalid), and detailed failures list
```

### 3. Retrieve Certificates (Presigned R2 Links)
- **Single PDF:** `GET /api/certificates/{cert_id}/download` → Returns 1-hour presigned direct download URL.
- **ZIP Bundle:** `GET /api/jobs/{job_id}/download` → Generates & returns presigned download URL for `zips/{job_id}.zip`.

---

## 5. Edge Cases Covered
- **Rapid Double-Clicks / Concurrent Submissions:** Partial unique index `uq_cert_email_title` on DB catches race conditions with `IntegrityError` → returns `409 Conflict`.
- **Re-Submitting Batches (Idempotency):** System queries existing `(title, recipient_email)` pairs, skips already-issued recipients with a message, and generates jobs only for new users.
- **Partial Batch Failures:** Per-item `try/except` loop commits progress individually so one bad recipient never aborts the remaining batch.
- **Malformed & Duplicate Data:** Bad emails, missing names, and intra-batch duplicates are marked `invalid` without blocking valid recipients. Batches >1000 items return `413`.
- **Unready / Failed Downloads:** Requesting ungenerated or failed certificates returns `409 Conflict` (never corrupt files). Non-existent IDs return `404`.
- **Extremely Long Text & Special Characters:** Dynamic font auto-scaling in ReportLab shrinks text size to fit printable certificate boundaries without truncation.
- **Unauthorized Access:** Missing or invalid `X-API-Key` returns `401` / `403` across all endpoints.
