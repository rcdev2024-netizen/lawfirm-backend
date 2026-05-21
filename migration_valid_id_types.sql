-- ============================================================
-- Philippine Valid ID Types — lookup catalog
-- Run in Supabase SQL Editor (Dashboard → SQL Editor → New Query)
--
-- Purpose:
--   valid_id_types  = dropdown options (this migration)
--   client_valid_ids = per-client uploaded IDs (already exists)
-- ============================================================

-- Widen id_type on client records to fit longer labels
ALTER TABLE client_valid_ids
    ALTER COLUMN id_type TYPE VARCHAR(100);

-- ── Lookup table ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS valid_id_types (
    id              BIGSERIAL PRIMARY KEY,
    name            VARCHAR(100) NOT NULL,
    category        VARCHAR(20) NOT NULL,
    display_order   INT NOT NULL DEFAULT 0,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT valid_id_types_name_unique UNIQUE (name),
    CONSTRAINT valid_id_types_category_check CHECK (
        category IN ('primary', 'secondary')
    )
);

CREATE INDEX IF NOT EXISTS idx_valid_id_types_category
    ON valid_id_types (category, display_order)
    WHERE is_active = TRUE;

-- ── PRIMARY GOVERNMENT IDs ────────────────────────────────────
INSERT INTO valid_id_types (name, category, display_order) VALUES
    ('Philippine Passport', 'primary', 1),
    ('PhilSys National ID', 'primary', 2),
    ('Driver''s License', 'primary', 3),
    ('UMID (Unified Multi-Purpose ID)', 'primary', 4),
    ('PRC ID', 'primary', 5),
    ('Postal ID', 'primary', 6),
    ('Voter''s ID', 'primary', 7),
    ('SSS ID', 'primary', 8),
    ('GSIS eCard', 'primary', 9),
    ('Senior Citizen ID', 'primary', 10),
    ('PWD ID', 'primary', 11),
    ('OWWA ID', 'primary', 12),
    ('OFW ID', 'primary', 13)
ON CONFLICT (name) DO UPDATE SET
    category = EXCLUDED.category,
    display_order = EXCLUDED.display_order,
    is_active = TRUE;

-- ── SECONDARY / SUPPORTING IDs ────────────────────────────────
INSERT INTO valid_id_types (name, category, display_order) VALUES
    ('TIN ID', 'secondary', 1),
    ('Barangay ID', 'secondary', 2),
    ('Company ID', 'secondary', 3),
    ('School ID', 'secondary', 4),
    ('Police Clearance', 'secondary', 5),
    ('NBI Clearance', 'secondary', 6),
    ('Birth Certificate', 'secondary', 7),
    ('Marriage Certificate', 'secondary', 8)
ON CONFLICT (name) DO UPDATE SET
    category = EXCLUDED.category,
    display_order = EXCLUDED.display_order,
    is_active = TRUE;
