-- Enable UUID extension if not enabled
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Table: jobs
CREATE TABLE IF NOT EXISTS jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    issued_by TEXT NOT NULL,
    issue_date DATE NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (
        status IN ('pending', 'processing', 'completed', 'completed_with_errors', 'failed')
    ),
    total_count INT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ
);

-- Table: certificates
CREATE TABLE IF NOT EXISTS certificates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    position INT NOT NULL,
    recipient_name TEXT NOT NULL,
    recipient_email TEXT NOT NULL,
    certificate_number TEXT UNIQUE,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (
        status IN ('pending', 'processing', 'success', 'failed', 'invalid')
    ),
    file_path TEXT,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    generated_at TIMESTAMPTZ
);

-- Indexes
CREATE INDEX IF NOT EXISTS ix_certificates_job_status ON certificates (job_id, status);
CREATE INDEX IF NOT EXISTS ix_certificates_job_id ON certificates (job_id);
