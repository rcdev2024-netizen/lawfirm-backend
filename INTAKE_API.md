# Client Intake API (v2.3)

Run `migration_client_intake.sql` in Supabase, then create a **private** Storage bucket named `intake-uploads`.

## Auth

All endpoints require `Authorization: Bearer <JWT>` and role `admin` or `attorney`.

### Upload endpoint

- **URL:** `POST /api/intake/uploads`
- **Multipart:** `file` (required), `draft_id` (optional), `category` (default `intake_form`)
- **OCR flow:** use `category=ocr_document`
- **Success:** JSON includes `id` and `upload_id` (same integer)
- **DB fix:** if `ocr_document` caused 500 before, run `migration_client_intake_upload_fix.sql` in Supabase

## Manual wizard flow

1. `POST /api/intake/drafts` — start draft (`source: "manual"`)
2. `PATCH /api/intake/drafts/{id}` — save step data in `draft_data` (personal, contact, valid_ids, case_info)
3. `POST /api/intake/drafts/{id}/validate?step=1` — validate step
4. `POST /api/intake/uploads` — upload photo/ID images (multipart)
5. `POST /api/intake/ai/duplicates` — check duplicates before save
6. `POST /api/intake/drafts/{id}/finalize` — create user + client profile

## OCR flow

1. `POST /api/intake/uploads` — upload scanned form (JPG/PNG/PDF)
2. `POST /api/intake/ocr/process` — `{ "upload_id": 1, "draft_id": 1 }`
3. `GET /api/intake/ocr/results/{extraction_id}` — review confidence scores
4. `POST /api/intake/ocr/apply` — `{ "extraction_id": 1, "draft_id": 1, "overwrite": false }`
5. Admin edits draft via `PATCH /api/intake/drafts/{id}`
6. `POST /api/intake/drafts/{id}/finalize` — **human must confirm**

Alternative: `POST /api/intake/ocr/map-from-text` with `{ "raw_text": "..." }` if using browser OCR.

## AI helpers

- `POST /api/intake/ai/duplicates`
- `POST /api/intake/ai/classify-case`
- `POST /api/intake/ai/suggestions`

## draft_data JSON shape

```json
{
  "personal": {
    "first_name": "Juan",
    "last_name": "Dela Cruz",
    "birth_date": "1985-03-21",
    "nationality": "Filipino"
  },
  "contact": {
    "email": "juan@example.com",
    "phone_number": "09171234567",
    "address": "123 Main St, Legazpi City"
  },
  "valid_ids": {
    "primary_id_type": "PhilSys ID",
    "primary_id_number": "1234-5678-9012",
    "profile_photo_url": "https://..."
  },
  "case_info": {
    "case_type": "Family Law",
    "notes": "Annulment consultation"
  }
}
```

## Environment

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | Optional — enables vision OCR on images |
| `OPENAI_OCR_MODEL` | Default `gpt-4o-mini` |
| `INTAKE_STORAGE_BUCKET` | Default `intake-uploads` |
| `INTAKE_MAX_FILE_MB` | Default `10` |
