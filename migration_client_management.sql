-- ============================================================
-- CLIENT MANAGEMENT — clients table as source of truth
-- Run in Supabase SQL Editor after migration_client_intake.sql
-- ============================================================

-- ── 1. New columns on clients ─────────────────────────────────
ALTER TABLE clients ADD COLUMN IF NOT EXISTS id BIGSERIAL;
ALTER TABLE clients ADD COLUMN IF NOT EXISTS full_name VARCHAR(255);
ALTER TABLE clients ADD COLUMN IF NOT EXISTS email VARCHAR(255);
ALTER TABLE clients ADD COLUMN IF NOT EXISTS phone_number VARCHAR(50);
ALTER TABLE clients ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE;
ALTER TABLE clients ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE clients ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP WITH TIME ZONE;

-- Ensure every row has id (BIGSERIAL fills new rows automatically)
UPDATE clients SET id = DEFAULT WHERE id IS NULL;

-- Backfill display fields from users + contact
UPDATE clients c SET
    full_name = COALESCE(c.full_name, u.full_name),
    email = COALESCE(c.email, u.email),
    phone_number = COALESCE(c.phone_number, cci.phone_number, u.phone)
FROM users u
LEFT JOIN client_contact_info cci ON cci.user_id = u.id
WHERE c.user_id = u.id;

-- ── 2. Primary key: id (keep user_id unique for login link) ───
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'clients_pkey' AND conrelid = 'clients'::regclass
    ) THEN
        ALTER TABLE clients DROP CONSTRAINT clients_pkey;
    END IF;
EXCEPTION WHEN OTHERS THEN
    NULL;
END $$;

ALTER TABLE clients ALTER COLUMN id SET NOT NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'clients_pkey'
    ) THEN
        ALTER TABLE clients ADD PRIMARY KEY (id);
    END IF;
END $$;

CREATE UNIQUE INDEX IF NOT EXISTS idx_clients_user_id ON clients(user_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_clients_email_active
    ON clients(email) WHERE is_deleted = FALSE AND email IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_clients_list
    ON clients (is_deleted, updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_clients_full_name
    ON clients (full_name) WHERE is_deleted = FALSE;

-- ── 3. updated_at trigger (if not already present) ──────────────
CREATE OR REPLACE FUNCTION update_intake_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_clients_updated ON clients;
CREATE TRIGGER trg_clients_updated
    BEFORE UPDATE ON clients
    FOR EACH ROW EXECUTE FUNCTION update_intake_updated_at();

-- ── 4. Staff roles (secretary) optional seed ───────────────────
INSERT INTO roles (name, display_name, description, is_system) VALUES
    ('secretary', 'Secretary', 'Front office — client encoding and scheduling', TRUE)
ON CONFLICT (name) DO NOTHING;
