-- ============================================================
-- Migration: Case Hearings with Multiple Dates & Reschedule Support
-- Run this in your Supabase SQL Editor (Dashboard > SQL Editor)
-- ============================================================

-- 1. Create case_hearings table
CREATE TABLE IF NOT EXISTS case_hearings (
    id BIGSERIAL PRIMARY KEY,
    case_id BIGINT NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    hearing_date DATE NOT NULL,
    hearing_time VARCHAR(50),
    court VARCHAR(255),
    judge VARCHAR(255),
    status VARCHAR(50) DEFAULT 'scheduled',
    notes TEXT,
    rescheduled_from_id BIGINT REFERENCES case_hearings(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_case_hearings_case_id ON case_hearings(case_id);
CREATE INDEX IF NOT EXISTS idx_case_hearings_hearing_date ON case_hearings(hearing_date);
CREATE INDEX IF NOT EXISTS idx_case_hearings_status ON case_hearings(status);
CREATE INDEX IF NOT EXISTS idx_case_hearings_rescheduled_from ON case_hearings(rescheduled_from_id);

-- 3. Add status constraint
ALTER TABLE case_hearings
  DROP CONSTRAINT IF EXISTS case_hearings_status_check;

ALTER TABLE case_hearings
  ADD CONSTRAINT case_hearings_status_check
  CHECK (status IN (
    'scheduled',
    'completed',
    'cancelled',
    'rescheduled',
    'postponed'
  ));

-- 4. Migrate existing hearing data from cases table to case_hearings
INSERT INTO case_hearings (case_id, hearing_date, hearing_time, court, judge, status, created_at)
SELECT 
    id as case_id,
    next_hearing_date as hearing_date,
    next_hearing_time as hearing_time,
    court,
    judge,
    CASE 
        WHEN next_hearing_date IS NULL THEN NULL
        ELSE 'scheduled'
    END as status,
    created_at
FROM cases
WHERE next_hearing_date IS NOT NULL;

-- 5. Remove redundant hearing date/time columns from cases table
-- Note: court and judge are kept as case-level attributes (primary court/judge for the case)
-- Individual hearings can have different court/judge if needed
ALTER TABLE cases DROP COLUMN IF EXISTS next_hearing_date;
ALTER TABLE cases DROP COLUMN IF EXISTS next_hearing_time;

-- 6. (Optional) Add a computed column for next_upcoming_hearing
-- This keeps a reference to the next scheduled hearing for quick access
-- ALTER TABLE cases ADD COLUMN next_hearing_id BIGINT REFERENCES case_hearings(id) ON DELETE SET NULL;
