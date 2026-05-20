-- ============================================================
-- Migration: Appointment Reschedule Support
-- Run this in your Supabase SQL Editor (Dashboard > SQL Editor)
-- ============================================================

-- 1. Add rescheduled_from_id column (self-referencing FK)
ALTER TABLE appointments
ADD COLUMN IF NOT EXISTS rescheduled_from_id INTEGER
  REFERENCES appointments(id) ON DELETE SET NULL;

-- 2. Index for fast lookups of rescheduled chains
CREATE INDEX IF NOT EXISTS idx_appointments_rescheduled_from
  ON appointments(rescheduled_from_id);

-- 3. Drop old status constraint (if it exists) and add updated one
--    that includes 'rescheduled' and 'expired'
ALTER TABLE appointments
  DROP CONSTRAINT IF EXISTS appointments_status_check;

ALTER TABLE appointments
  ADD CONSTRAINT appointments_status_check
  CHECK (status IN (
    'pending',
    'confirmed',
    'cancelled',
    'completed',
    'rescheduled',
    'expired'
  ));
