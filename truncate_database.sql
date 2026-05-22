-- ============================================================
-- DATABASE TRUNCATION SCRIPT
-- WARNING: This will DELETE ALL DATA from all tables
-- Run this in Supabase SQL Editor: Dashboard → SQL Editor → New Query
-- ============================================================

-- Disable foreign key constraints temporarily
SET session_replication_role = 'replica';

-- Truncate all tables in dependency order (child tables first)
TRUNCATE TABLE intake_ai_logs CASCADE;
TRUNCATE TABLE intake_extraction_results CASCADE;
TRUNCATE TABLE client_intake_drafts CASCADE;
TRUNCATE TABLE intake_uploads CASCADE;
TRUNCATE TABLE client_photos CASCADE;
TRUNCATE TABLE client_valid_ids CASCADE;
TRUNCATE TABLE client_intake_cases CASCADE;
TRUNCATE TABLE client_contact_info CASCADE;
TRUNCATE TABLE clients CASCADE;
TRUNCATE TABLE documents CASCADE;
TRUNCATE TABLE messages CASCADE;
TRUNCATE TABLE invoices CASCADE;
TRUNCATE TABLE notifications CASCADE;
TRUNCATE TABLE appointments CASCADE;
TRUNCATE TABLE cases CASCADE;
TRUNCATE TABLE role_audit_log CASCADE;
TRUNCATE TABLE role_permissions CASCADE;
TRUNCATE TABLE users CASCADE;
TRUNCATE TABLE audit_logs CASCADE;

-- Re-enable foreign key constraints
SET session_replication_role = 'origin';

-- Reset sequences
ALTER SEQUENCE users_id_seq RESTART WITH 1;
ALTER SEQUENCE appointments_id_seq RESTART WITH 1;
ALTER SEQUENCE cases_id_seq RESTART WITH 1;
ALTER SEQUENCE documents_id_seq RESTART WITH 1;
ALTER SEQUENCE messages_id_seq RESTART WITH 1;
ALTER SEQUENCE notifications_id_seq RESTART WITH 1;
ALTER SEQUENCE invoices_id_seq RESTART WITH 1;
ALTER SEQUENCE roles_id_seq RESTART WITH 1;
ALTER SEQUENCE role_permissions_id_seq RESTART WITH 1;
ALTER SEQUENCE role_audit_log_id_seq RESTART WITH 1;
ALTER SEQUENCE client_intake_drafts_id_seq RESTART WITH 1;
ALTER SEQUENCE clients_id_seq RESTART WITH 1;
ALTER SEQUENCE client_valid_ids_id_seq RESTART WITH 1;
ALTER SEQUENCE client_intake_cases_id_seq RESTART WITH 1;
ALTER SEQUENCE client_photos_id_seq RESTART WITH 1;
ALTER SEQUENCE intake_uploads_id_seq RESTART WITH 1;
ALTER SEQUENCE intake_extraction_results_id_seq RESTART WITH 1;
ALTER SEQUENCE intake_ai_logs_id_seq RESTART WITH 1;
ALTER SEQUENCE audit_logs_id_seq RESTART WITH 1;
ALTER SEQUENCE valid_id_types_id_seq RESTART WITH 1;

-- Re-seed roles (required for admin user)
INSERT INTO roles (name, display_name, description, is_system) VALUES
    ('guest',     'Guest',     'Unauthenticated or limited-access visitor',                    TRUE),
    ('client',    'Client',    'Law firm client with access to their own cases and documents', TRUE),
    ('paralegal', 'Paralegal', 'Supports attorneys with case preparation and research',        TRUE),
    ('attorney',  'Attorney',  'Licensed lawyer with full case and calendar access',           TRUE),
    ('admin',     'Admin',     'Full system administrator with access to all firm operations', TRUE)
ON CONFLICT (name) DO NOTHING;

-- Re-seed role permissions
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

-- Re-seed valid ID types
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
    ('OFW ID', 'primary', 13),
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

-- ============================================================
-- DATABASE TRUNCATION COMPLETE
-- All tables have been truncated and re-seeded with reference data
-- ============================================================
