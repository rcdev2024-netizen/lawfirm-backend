-- ============================================================
-- LAW FIRM MIGRATION v3
-- Adds: approval_status to users, appointment_type + specialization
-- Run in Supabase SQL Editor: Dashboard → SQL Editor → New Query
-- ============================================================

-- 1. Add approval_status to users table
--    pending  = self-registered client waiting for admin approval
--    approved = approved by admin (or admin-created account)
--    rejected = rejected by admin
ALTER TABLE users ADD COLUMN IF NOT EXISTS approval_status VARCHAR(20) DEFAULT 'approved';

-- Set existing client registrations to approved by default
-- (adjust if you want to retroactively set all clients to pending)
UPDATE users SET approval_status = 'approved' WHERE approval_status IS NULL;

-- 2. Add appointment_type to appointments table
--    online  = virtual / video call appointment
--    onsite  = in-person at the office
ALTER TABLE appointments ADD COLUMN IF NOT EXISTS appointment_type VARCHAR(20) DEFAULT 'onsite';

UPDATE appointments SET appointment_type = 'onsite' WHERE appointment_type IS NULL;

-- 3. Add specialization to users table (for attorneys)
ALTER TABLE users ADD COLUMN IF NOT EXISTS specialization VARCHAR(255);

-- ============================================================
-- INDEXES
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_users_approval_status ON users(approval_status);
CREATE INDEX IF NOT EXISTS idx_appointments_attorney_id ON appointments(attorney_id);
CREATE INDEX IF NOT EXISTS idx_appointments_type ON appointments(appointment_type);
