-- ============================================================
-- LAW FIRM MIGRATION - Audit Logs Table
-- Run this in Supabase SQL Editor: Dashboard → SQL Editor → New Query
-- ============================================================

CREATE TABLE IF NOT EXISTS audit_logs (
    id           BIGSERIAL    PRIMARY KEY,
    user_id      BIGINT       REFERENCES users(id) ON DELETE SET NULL,
    user_name    VARCHAR(255),
    action       VARCHAR(100) NOT NULL,
    entity_type  VARCHAR(100),
    entity_id    BIGINT,
    description  TEXT,
    ip_address   VARCHAR(50),
    created_at   TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id    ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action     ON audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_logs_entity     ON audit_logs(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at DESC);
