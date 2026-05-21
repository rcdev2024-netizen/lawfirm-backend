-- Run once if intake_uploads already exists (fixes ocr_document category 500)
ALTER TABLE intake_uploads DROP CONSTRAINT IF EXISTS chk_upload_category;
ALTER TABLE intake_uploads ADD CONSTRAINT chk_upload_category CHECK (
    upload_category IN (
        'intake_form', 'valid_id_primary', 'valid_id_secondary',
        'profile_photo', 'other', 'ocr_document'
    )
);
