-- ============================================================
-- CREATE ADMIN USER
-- Run this AFTER truncate_database.sql in Supabase SQL Editor
-- ============================================================

-- Insert admin user
-- Password: admin123 (change this after first login)
-- Email: admin@lawfirm.com (change this as needed)
INSERT INTO users (
    full_name,
    email,
    hashed_password,
    role_id,
    phone,
    is_active,
    approval_status,
    specialization
) VALUES (
    'System Administrator',
    'admin@lawfirm.com',
    '$2b$12$7ggWAcwe3saMYxSoS8ACxOoDQ.nZH6SF7pz4d3PH5Db.9xVuL8n.u', -- bcrypt hash for 'admin123'
    (SELECT id FROM roles WHERE name = 'admin'),
    '+639123456789',
    TRUE,
    'approved',
    'System Administration'
);

-- ============================================================
-- ADMIN USER CREATED
-- Email: admin@lawfirm.com
-- Password: admin123
-- Role: admin
-- ============================================================
