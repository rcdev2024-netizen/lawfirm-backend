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
| GET | `/api/clients/{id}` | Full profile + `contact` + `valid_ids` (signed image URLs) |
| PATCH | `/api/clients/{id}` | Edit personal, contact, valid_ids |
| POST | `/api/clients/{id}/uploads` | Multipart `file` + `category` → `{ upload_id, url }` |
| DELETE | `/api/clients/{id}` | Soft delete (`is_deleted`, `deleted_at`) |

### GET detail — `valid_ids` object

Signed HTTPS URLs (regenerated on each read from `intake-uploads`):

```json
"valid_ids": {
  "primary_id_type": "Driver's License",
  "primary_id_number": "...",
  "primary_id_image_url": "https://...",
  "secondary_id_type": null,
  "secondary_id_number": null,
  "secondary_id_image_url": null
}
```

### Upload categories

`profile_photo`, `valid_id_primary`, `valid_id_secondary`

**Removed:** `PATCH /api/clients/{id}/approval`, `POST /api/clients` (use intake finalize)

## Case Management note

`POST /api/cases` still uses **`client_id` = `users.id`** (portal account id).

List/search responses include both:

- `id` — `clients.id` (use in Client Management UI)
- `user_id` — use when creating cases in Case Management today

## Intake finalize

Creates `users` + `clients` row with `full_name`, `email`, `phone_number`, `profile_photo_url`, active immediately.

Returns `client_id` = **`clients.id`**.
