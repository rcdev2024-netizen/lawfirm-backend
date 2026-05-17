-- ============================================================
-- LAW FIRM ROLE MIGRATION v2
-- Run this in Supabase SQL Editor: Dashboard → SQL Editor → New Query
-- Adds a proper roles table and links users.role_id as a FK.
-- Safe to run on both fresh databases and existing ones.
-- ============================================================

-- ── 1. ROLES TABLE ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS roles (
    id           BIGSERIAL    PRIMARY KEY,
    name         VARCHAR(100) UNIQUE NOT NULL,
    display_name VARCHAR(150) NOT NULL,
    description  TEXT,
    is_system    BOOLEAN      DEFAULT FALSE,
    is_active    BOOLEAN      DEFAULT TRUE,
    created_at   TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at   TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ── 2. SEED SYSTEM ROLES ─────────────────────────────────────
INSERT INTO roles (name, display_name, description, is_system) VALUES
    ('guest',     'Guest',     'Unauthenticated or limited-access visitor',                    TRUE),
    ('client',    'Client',    'Law firm client with access to their own cases and documents', TRUE),
    ('paralegal', 'Paralegal', 'Supports attorneys with case preparation and research',        TRUE),
    ('attorney',  'Attorney',  'Licensed lawyer with full case and calendar access',           TRUE),
    ('admin',     'Admin',     'Full system administrator with access to all firm operations', TRUE)
ON CONFLICT (name) DO NOTHING;

-- ── 3. ROLE PERMISSIONS TABLE ─────────────────────────────────
CREATE TABLE IF NOT EXISTS role_permissions (
    id          BIGSERIAL    PRIMARY KEY,
    role_name   VARCHAR(100) NOT NULL REFERENCES roles(name) ON DELETE CASCADE ON UPDATE CASCADE,
    permission  VARCHAR(255) NOT NULL,
    created_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE (role_name, permission)
);

-- ── 4. SEED DEFAULT PERMISSIONS ──────────────────────────────
INSERT INTO role_permissions (role_name, permission) VALUES
    ('guest',     'appointments:create'),
    ('guest',     'documents:read_public'),
    ('client',    'appointments:create'),
    ('client',    'appointments:read_own'),
    ('client',    'cases:read_own'),
    ('client',    'documents:read_own'),
    ('client',    'documents:upload_own'),
    ('client',    'messages:send'),
    ('client',    'messages:read_own'),
    ('client',    'invoices:read_own'),
    ('client',    'notifications:read_own'),
    ('client',    'profile:update_own'),
    ('paralegal', 'appointments:create'),
    ('paralegal', 'appointments:read_own'),
    ('paralegal', 'appointments:read_assigned'),
    ('paralegal', 'cases:read_assigned'),
    ('paralegal', 'cases:update_assigned'),
    ('paralegal', 'documents:read_assigned'),
    ('paralegal', 'documents:upload_assigned'),
    ('paralegal', 'messages:send'),
    ('paralegal', 'messages:read_own'),
    ('paralegal', 'notifications:read_own'),
    ('paralegal', 'profile:update_own'),
    ('attorney',  'appointments:create'),
    ('attorney',  'appointments:read_own'),
    ('attorney',  'appointments:read_assigned'),
    ('attorney',  'appointments:update_assigned'),
    ('attorney',  'cases:read_assigned'),
    ('attorney',  'cases:create'),
    ('attorney',  'cases:update_assigned'),
    ('attorney',  'documents:read_assigned'),
    ('attorney',  'documents:upload_assigned'),
    ('attorney',  'messages:send'),
    ('attorney',  'messages:read_own'),
    ('attorney',  'invoices:read_assigned'),
    ('attorney',  'notifications:read_own'),
    ('attorney',  'profile:update_own'),
    ('admin',     'appointments:*'),
    ('admin',     'cases:*'),
    ('admin',     'documents:*'),
    ('admin',     'messages:*'),
    ('admin',     'invoices:*'),
    ('admin',     'notifications:*'),
    ('admin',     'users:*'),
    ('admin',     'roles:*'),
    ('admin',     'analytics:*'),
    ('admin',     'audit:*'),
    ('admin',     'profile:update_own')
ON CONFLICT (role_name, permission) DO NOTHING;

-- ── 5. ADD role_id COLUMN TO USERS ────────────────────────────
-- Add nullable first so existing rows don't break.
ALTER TABLE users ADD COLUMN IF NOT EXISTS role_id BIGINT;

-- ── 6. BACKFILL role_id FROM EXISTING role VARCHAR ────────────
-- If users already has a `role` text column, map it to the new FK.
UPDATE users u
SET role_id = r.id
FROM roles r
WHERE r.name = COALESCE(u.role, 'client')
  AND u.role_id IS NULL;

-- Fallback: any row still NULL gets 'client'
UPDATE users u
SET role_id = (SELECT id FROM roles WHERE name = 'client')
WHERE u.role_id IS NULL;

-- ── 7. ENFORCE NOT NULL + FOREIGN KEY ─────────────────────────
ALTER TABLE users ALTER COLUMN role_id SET NOT NULL;

ALTER TABLE users
    ADD CONSTRAINT IF NOT EXISTS users_role_id_fkey
    FOREIGN KEY (role_id)
    REFERENCES roles(id)
    ON UPDATE CASCADE
    ON DELETE RESTRICT;

-- ── 8. DROP OLD role VARCHAR COLUMN ───────────────────────────
-- Only runs if the old column exists.
-- Comment this out if you want a transition period before removing it.
ALTER TABLE users DROP COLUMN IF EXISTS role;

-- ── 9. ROLE CHANGE AUDIT LOG ──────────────────────────────────
CREATE TABLE IF NOT EXISTS role_audit_log (
    id          BIGSERIAL PRIMARY KEY,
    user_id     BIGINT    NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    changed_by  BIGINT    REFERENCES users(id) ON DELETE SET NULL,
    old_role_id BIGINT    REFERENCES roles(id) ON DELETE SET NULL,
    new_role_id BIGINT    NOT NULL REFERENCES roles(id) ON DELETE RESTRICT,
    reason      TEXT,
    changed_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ── 10. INDEXES ───────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_users_role_id              ON users(role_id);
CREATE INDEX IF NOT EXISTS idx_role_permissions_role      ON role_permissions(role_name);
CREATE INDEX IF NOT EXISTS idx_role_audit_log_user_id     ON role_audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_role_audit_log_changed_by  ON role_audit_log(changed_by);
