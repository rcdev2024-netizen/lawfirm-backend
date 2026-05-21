# Client Intake API (v2.3) — 3-step wizard

Run `migration_client_intake.sql` + `migration_client_intake_upload_fix.sql` in Supabase.  
Create private Storage bucket: **`intake-uploads`**.

## Wizard steps (3 only)

| Step | Section | Content |
|------|---------|---------|
| 1 | `personal` | Name, birth date, nationality, etc. |
| 2 | `contact` | Email, phone, address |
| 3 | `valid_ids` | Primary/secondary ID, profile photo |

**Cases are not part of intake.** Create cases later via `POST /api/cases` with `client_id` (one client, many cases).

## Auth

- Base path: **`/api/intake/*`**
- Header: `Authorization: Bearer <JWT>`
- Roles: **`admin`** or **`attorney`** only

## PATCH drafts — partial step saves

`PATCH /api/intake/drafts/{id}`

```json
{
  "current_step": 2,
  "draft_data": {
    "contact": { "email": "juan@example.com", "phone_number": "09171234567", "address": "Legazpi City" }
  }
}
```

- Server **merges** partial `draft_data` (only `personal`, `contact`, or `valid_ids`).
- Validates **only sections sent** — never `case_info`.
- `current_step`: **1–3** only.
- Validation failure: **422** with `detail` array.

## Validate step

`POST /api/intake/drafts/{id}/validate?step=1|2|3`

## Upload

`POST /api/intake/uploads` (multipart) — see previous docs.

## valid_ids (step 3)

- `profile_photo_upload_id`, `primary_id_image_upload_id`, `secondary_id_image_upload_id`
- Or URL fields resolved on finalize.

## AI suggestions

`POST /api/intake/ai/suggestions` — `{ "draft_data", "current_step": 1|2|3 }`

## OCR

Optional; may still extract `caseType` into draft for display, but intake does not require or save cases.

## Finalize

`POST /api/intake/drafts/{id}/finalize`

- Validates steps **1–3 only** (personal, contact, valid_ids).
- Creates `users` + `clients` + `client_contact_info` + `client_valid_ids` / photos.
- Does **not** insert `client_intake_cases` or require `case_info`.

```json
{ "client_id": 1, "user_id": 1, "email": "...", "temporary_password": "...", "full_name": "..." }
```

Use `client_id` when creating cases: `POST /api/cases` with `client_id`.

## draft_data sections

- `personal`, `contact`, `valid_ids` only (ignore `case_info` if sent)

## Valid ID types

`GET /api/intake/id-types` — run `migration_valid_id_types.sql`

## Smoke test

1. `POST /api/intake/drafts` `{ "source": "manual", "current_step": 1 }`
2. `PATCH` only `personal` → no `contact.email` errors
3. `PATCH` only `contact` on step 2
4. `PATCH` only `valid_ids` on step 3
5. `POST /finalize` — client created, no case row
