# Client Management API

`clients` table is the **source of truth** after intake. No approval workflow.

## Migration to run

**`migration_client_management.sql`** (after `migration_client_intake.sql`)

## Auth

Staff roles: `admin`, `attorney`, `secretary`, `paralegal`

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/clients` | Paginated list (`is_deleted=false` default) |
| GET | `/api/clients/search?q=` | Quick search |
| GET | `/api/clients/{id}` | Full profile + `contact` |
| PATCH | `/api/clients/{id}` | Edit; sets `updated_at` |
| DELETE | `/api/clients/{id}` | Soft delete (`is_deleted`, `deleted_at`) |

**Removed:** `PATCH /api/clients/{id}/approval`, `POST /api/clients` (use intake finalize)

## Case Management note

`POST /api/cases` still uses **`client_id` = `users.id`** (portal account id).

List/search responses include both:

- `id` — `clients.id` (use in Client Management UI)
- `user_id` — use when creating cases in Case Management today

## Intake finalize

Creates `users` + `clients` row with `full_name`, `email`, `phone_number`, `profile_photo_url`, active immediately.

Returns `client_id` = **`clients.id`**.
