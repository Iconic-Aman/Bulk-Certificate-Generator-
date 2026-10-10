# Bulk Certificate Generator

A backend service that creates PDF certificates in bulk, saves them in cloud storage, and lets you download them one-by-one or all together in a ZIP file.

---

## 1. How It Works
- **Fast and Non-Blocking:** When you upload names, the server gives you a Job ID right away and creates PDFs in the background.
- **Safe from Crashes:** If one person has bad data, only their certificate fails. Everyone else still gets theirs.
- **Cloud Storage:** PDFs are saved to Cloudflare R2 and given out via temporary download links.
- **Live Progress:** Check your Job ID anytime to see how many certificates are done, pending, or failed.

---

## 2. Setup & Run

### Environment Setup (`.env`)
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

### Run Locally
```bash
cd app && uv sync
uv run uvicorn main:app --reload --port 8000   # Swagger UI: http://localhost:8000/api/docs

# Run all automated tests
uv run pytest tests -v
```

---

## 3. How to Use the API (Header: `X-API-Key: <key>`)

### 1. Create Certificates (JSON or File)
- **Send JSON (`POST /api/jobs`):**
```bash
curl -X POST "http://localhost:8000/api/jobs" -H "Content-Type: application/json" -H "X-API-Key: key" -d '{
  "title": "Web Development", "issued_by": "Acme School",
  "recipients": [{"name": "Alice", "email": "alice@example.com", "issue_date": "2026-10-09"}]
}'
```
- **Upload File (`POST /api/jobs/upload`):** Upload a `.json` file with names and emails directly.

### 2. Check Job Status (`GET /api/jobs/{job_id}`)
See progress percent, counts of finished certificates, and details on any failed rows.

### 3. Download Certificates
- **Single Certificate:** `GET /api/certificates/{cert_id}/download` (returns direct PDF link).
- **All in one ZIP:** `GET /api/jobs/{job_id}/download` (packs all successful PDFs into one ZIP file).

---

## 4. Edge Cases Handled
- **Clicking Submit Twice:** The database catches double submissions immediately and stops duplicate work.
- **Uploading Same People Again:** Skips people who already received a certificate for that course and only creates new ones.
- **Bad or Missing Data:** Wrong email format or empty names are cleanly flagged without stopping other valid certificates.
- **Downloading Before Ready:** Blocks download requests until files are ready, so you never get broken files.
- **Super Long Names:** Shrinks text size automatically so long names fit cleanly on the certificate.
- **Wrong or Missing Password:** Blocks unauthenticated requests with `401` or `403`.

---

## 5. Further Improvements
- **Login with Google/GitHub (OAuth):** Allow users to sign in with their own accounts instead of sharing one fixed API key.
- **Upload Excel Files (`.xlsx`, `.csv`):** Let users upload spreadsheet files directly without having to convert them to JSON first.

---

## 6. Performance & Speed (100 Certificates Test)

| Step | Time Taken | What was done |
| :--- | :--- | :--- |
| **First Try (Baseline)** | 157.0s (~1.57s per cert) | Initial sequential generation: recreated cloud storage connections and made separate database commits for every single row. |
| **Thread Pool + Batch Commits** | **38.07s (~0.38s per cert)** | Added 10-thread worker pool for parallel PDF generation & R2 upload, cached S3 connection, and batched DB commits every 20 rows (4.1x faster). |
