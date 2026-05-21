-- ============================================================
-- CLIENT INTAKE MIGRATION v4
-- Run in Supabase SQL Editor (Dashboard → SQL Editor → New Query)
-- Also create Storage bucket: intake-uploads (private)
-- ============================================================

-- ── 1. CLIENT INTAKE DRAFTS (wizard + OCR review before save) ──
CREATE TABLE IF NOT EXISTS client_intake_drafts (
    id                  BIGSERIAL PRIMARY KEY,
    created_by          BIGINT REFERENCES users(id) ON DELETE SET NULL,
    status              VARCHAR(20) NOT NULL DEFAULT 'draft',
    current_step        INT NOT NULL DEFAULT 1,
    source              VARCHAR(20) NOT NULL DEFAULT 'manual',
    draft_data          JSONB NOT NULL DEFAULT '{}',
    intake_upload_id    BIGINT,
    extraction_id       BIGINT,
    user_id             BIGINT REFERENCES users(id) ON DELETE SET NULL,
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT chk_draft_status CHECK (status IN ('draft', 'submitted', 'abandoned'))
);

CREATE INDEX IF NOT EXISTS idx_intake_drafts_created_by ON client_intake_drafts(created_by);
CREATE INDEX IF NOT EXISTS idx_intake_drafts_status ON client_intake_drafts(status);

-- ── 2. CLIENT PROFILE (extends users — 1:1) ───────────────────
CREATE TABLE IF NOT EXISTS clients (
    user_id             BIGINT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    first_name          VARCHAR(100),
    middle_name         VARCHAR(100),
    last_name           VARCHAR(100) NOT NULL,
    suffix              VARCHAR(20),
    gender              VARCHAR(20),
    birth_date          DATE,
    civil_status        VARCHAR(50),
    nationality         VARCHAR(100),
    place_of_birth      VARCHAR(255),
    occupation          VARCHAR(255),
    client_status       VARCHAR(20) DEFAULT 'prospect',
    priority_level      VARCHAR(20) DEFAULT 'medium',
    tags                TEXT[] DEFAULT '{}',
    referred_by         VARCHAR(255),
    profile_photo_url   TEXT,
    photo_uploaded_at   TIMESTAMP WITH TIME ZONE,
    photo_uploaded_by   BIGINT REFERENCES users(id) ON DELETE SET NULL,
    photo_metadata      JSONB DEFAULT '{}',
    intake_completed_at TIMESTAMP WITH TIME ZONE,
    intake_completed_by BIGINT REFERENCES users(id) ON DELETE SET NULL,
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT chk_client_status CHECK (client_status IN ('prospect', 'active', 'closed')),
    CONSTRAINT chk_priority CHECK (priority_level IN ('low', 'medium', 'high', 'urgent'))
);

CREATE INDEX IF NOT EXISTS idx_clients_last_name ON clients(last_name);
CREATE INDEX IF NOT EXISTS idx_clients_status ON clients(client_status);

-- ── 3. CLIENT CONTACT INFO ────────────────────────────────────
CREATE TABLE IF NOT EXISTS client_contact_info (
    user_id             BIGINT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    email               VARCHAR(255),
    phone_number        VARCHAR(50),
    alternate_phone     VARCHAR(50),
    address             TEXT,
    barangay            VARCHAR(100),
    city                VARCHAR(100),
    province            VARCHAR(100),
    zip_code            VARCHAR(20),
    country             VARCHAR(100) DEFAULT 'Philippines',
    updated_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_client_contact_email ON client_contact_info(email);
CREATE INDEX IF NOT EXISTS idx_client_contact_phone ON client_contact_info(phone_number);

-- ── 4. VALID IDs ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS client_valid_ids (
    id                  BIGSERIAL PRIMARY KEY,
    user_id             BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    id_type             VARCHAR(50) NOT NULL,
    id_number           VARCHAR(100) NOT NULL,
    id_image_url        TEXT,
    is_primary          BOOLEAN DEFAULT FALSE,
    uploaded_at         TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    uploaded_by         BIGINT REFERENCES users(id) ON DELETE SET NULL,
    image_metadata      JSONB DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_client_valid_ids_user ON client_valid_ids(user_id);

-- ── 5. INTAKE CASE INFO (initial case at onboarding) ──────────
CREATE TABLE IF NOT EXISTS client_intake_cases (
    id                  BIGSERIAL PRIMARY KEY,
    user_id             BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    case_type           VARCHAR(100) NOT NULL,
    case_category       VARCHAR(100),
    consultation_date   DATE,
    assigned_lawyer_id  BIGINT REFERENCES users(id) ON DELETE SET NULL,
    referred_by         VARCHAR(255),
    notes               TEXT,
    priority_level      VARCHAR(20) DEFAULT 'medium',
    client_status       VARCHAR(20) DEFAULT 'prospect',
    tags                TEXT[] DEFAULT '{}',
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_client_intake_cases_user ON client_intake_cases(user_id);

-- ── 6. CLIENT PHOTOS (history / versions) ─────────────────────
CREATE TABLE IF NOT EXISTS client_photos (
    id                  BIGSERIAL PRIMARY KEY,
    user_id             BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    photo_url           TEXT NOT NULL,
    uploaded_at         TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    uploaded_by         BIGINT REFERENCES users(id) ON DELETE SET NULL,
    image_metadata      JSONB DEFAULT '{}',
    is_current          BOOLEAN DEFAULT TRUE,
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_client_photos_user ON client_photos(user_id);

-- ── 7. INTAKE UPLOADS (forms, IDs, scans) ─────────────────────
CREATE TABLE IF NOT EXISTS intake_uploads (
    id                  BIGSERIAL PRIMARY KEY,
    uploaded_by         BIGINT REFERENCES users(id) ON DELETE SET NULL,
    draft_id            BIGINT REFERENCES client_intake_drafts(id) ON DELETE SET NULL,
    file_name           VARCHAR(255) NOT NULL,
    file_type           VARCHAR(100),
    file_size           BIGINT,
    storage_path        TEXT NOT NULL,
    public_url          TEXT,
    upload_category     VARCHAR(50) DEFAULT 'intake_form',
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT chk_upload_category CHECK (
        upload_category IN (
            'intake_form', 'valid_id_primary', 'valid_id_secondary',
            'profile_photo', 'other', 'ocr_document'
        )
    )
);

CREATE INDEX IF NOT EXISTS idx_intake_uploads_draft ON intake_uploads(draft_id);

-- ── 8. OCR / AI EXTRACTION RESULTS ────────────────────────────
CREATE TABLE IF NOT EXISTS intake_extraction_results (
    id                  BIGSERIAL PRIMARY KEY,
    upload_id           BIGINT REFERENCES intake_uploads(id) ON DELETE CASCADE,
    draft_id            BIGINT REFERENCES client_intake_drafts(id) ON DELETE SET NULL,
    status              VARCHAR(30) NOT NULL DEFAULT 'pending',
    raw_text            TEXT,
    extracted_fields    JSONB DEFAULT '{}',
    field_confidence    JSONB DEFAULT '{}',
    mapped_fields       JSONB DEFAULT '{}',
    provider            VARCHAR(50),
    error_message       TEXT,
    reviewed            BOOLEAN DEFAULT FALSE,
    reviewed_by         BIGINT REFERENCES users(id) ON DELETE SET NULL,
    reviewed_at         TIMESTAMP WITH TIME ZONE,
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT chk_extraction_status CHECK (
        status IN ('pending', 'processing', 'completed', 'failed', 'requires_review')
    )
);

CREATE INDEX IF NOT EXISTS idx_extraction_upload ON intake_extraction_results(upload_id);
CREATE INDEX IF NOT EXISTS idx_extraction_draft ON intake_extraction_results(draft_id);

-- ── 9. AI ACTIVITY LOGS ───────────────────────────────────────
CREATE TABLE IF NOT EXISTS intake_ai_logs (
    id                  BIGSERIAL PRIMARY KEY,
    draft_id            BIGINT REFERENCES client_intake_drafts(id) ON DELETE SET NULL,
    user_id             BIGINT REFERENCES users(id) ON DELETE SET NULL,
    action              VARCHAR(100) NOT NULL,
    input_summary       TEXT,
    output_summary      JSONB DEFAULT '{}',
    performed_by        BIGINT REFERENCES users(id) ON DELETE SET NULL,
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_intake_ai_logs_draft ON intake_ai_logs(draft_id);

-- ── 10. FK back-references on drafts ──────────────────────────
ALTER TABLE client_intake_drafts
    DROP CONSTRAINT IF EXISTS fk_draft_upload;
ALTER TABLE client_intake_drafts
    ADD CONSTRAINT fk_draft_upload
    FOREIGN KEY (intake_upload_id) REFERENCES intake_uploads(id) ON DELETE SET NULL;

ALTER TABLE client_intake_drafts
    DROP CONSTRAINT IF EXISTS fk_draft_extraction;
ALTER TABLE client_intake_drafts
    ADD CONSTRAINT fk_draft_extraction
    FOREIGN KEY (extraction_id) REFERENCES intake_extraction_results(id) ON DELETE SET NULL;

-- ── 11. updated_at trigger helper ─────────────────────────────
CREATE OR REPLACE FUNCTION update_intake_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_client_intake_drafts_updated ON client_intake_drafts;
CREATE TRIGGER trg_client_intake_drafts_updated
    BEFORE UPDATE ON client_intake_drafts
    FOR EACH ROW EXECUTE FUNCTION update_intake_updated_at();

DROP TRIGGER IF EXISTS trg_clients_updated ON clients;
CREATE TRIGGER trg_clients_updated
    BEFORE UPDATE ON clients
    FOR EACH ROW EXECUTE FUNCTION update_intake_updated_at();
