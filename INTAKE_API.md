# Client Intake API (v2.3) — Angular-aligned

Run `migration_client_intake.sql` + `migration_client_intake_upload_fix.sql` in Supabase.  
Create private Storage bucket: **`intake-uploads`**.

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
    "personal": { "first_name": "Juan", "last_name": "Dela Cruz", "birth_date": "1985-03-21", "nationality": "Filipino" }
  }
}
```

- Server **merges** partial `draft_data` into existing JSON (does not replace whole draft).
- Validates **only sections sent** in `draft_data` (e.g. only `personal` → no `contact.email` errors).
- Validation failure: **422** with FastAPI-style `detail` array:
  ```json
  { "detail": [{ "loc": ["body","draft_data","personal","first_name"], "msg": "First name is required", "type": "value_error" }] }
  ```

## Validate step

`POST /api/intake/drafts/{id}/validate?step=1|2|3|4`

- Validates **that step only**.
- Response: `{ "step": 1, "valid": true, "errors": [] }` or `errors: [{ "field": "personal.first_name", "message": "..." }]`

## Upload

`POST /api/intake/uploads` (multipart)

| Field | Description |
|-------|-------------|
| `file` | JPG, PNG, WEBP, PDF |
| `draft_id` | Required for OCR flow |
| `category` | `profile_photo`, `valid_id_primary`, `valid_id_secondary`, `ocr_document`, `intake_form`, `other` |

Success **200/201**:

```json
{ "id": 1, "upload_id": 1, "url": "https://...", "storage_path": "...", "upload_category": "ocr_document" }
```

## valid_ids (step 3)

Accepts upload IDs (resolved to URLs on finalize):

- `profile_photo_upload_id`
- `primary_id_image_upload_id`
- `secondary_id_image_upload_id`

Or direct URLs: `profile_photo_url`, `primary_id_image_url`, etc.

## AI suggestions

`POST /api/intake/ai/suggestions`

```json
{ "draft_data": { "personal": { ... } }, "current_step": 1 }
```

- Hints for **current step only** (no errors for empty future steps).
- Response: `{ "suggestions": [{ "field": "personal.first_name", "message": "...", "severity": "info|warning|error" }], "is_ready_to_finalize": false }`

## OCR

1. `POST /api/intake/ocr/process` — `{ "upload_id": 1, "draft_id": 1 }`  
   → `{ "id": 1, "extraction_id": 1, "status": "processing|completed|failed" }`

2. `GET /api/intake/ocr/results/{id}`  
   → `{ "status": "...", "fields": [{ "field", "label", "value", "confidence": 0-100 }], "openai_available": true }`

3. `POST /api/intake/ocr/apply` — `{ "extraction_id", "draft_id", "overwrite": false }` — merges into draft, does not finalize.

## Finalize

`POST /api/intake/drafts/{id}/finalize`

- Validates **all 4 steps**.
- Creates `users` row with role **client** only.

```json
{ "client_id": 1, "user_id": 1, "email": "...", "temporary_password": "...", "full_name": "..." }
```

## draft_data sections (snake_case)

- `personal`, `contact`, `valid_ids`, `case_info`

## Environment

| Variable | Required |
|----------|----------|
| `SUPABASE_URL` | Yes |
| `SUPABASE_SERVICE_KEY` | Yes |
| `SECRET_KEY` | Yes |
| `INTAKE_STORAGE_BUCKET` | `intake-uploads` |
| `INTAKE_MAX_FILE_MB` | `4` on Vercel |
| `OPENAI_API_KEY` | Optional (OCR) |

## Smoke test

1. `POST /api/intake/drafts` `{ "source": "manual", "current_step": 1 }`
2. `PATCH` with only `personal` → **422 must NOT** mention `contact.email`
3. `POST /api/intake/uploads` `category=ocr_document`
4. `POST /api/intake/ai/suggestions` `current_step=1` → step-1 hints only
5. `POST /finalize` after all steps complete
