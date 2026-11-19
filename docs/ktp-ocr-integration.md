# BAS-AI KTP OCR Integration

## Scope
Add a KTP capture/OCR module to the isolated Laravel sandbox route `/basai/test`, above the existing audio upload/recording controls.

The team-owned BAS-AI page and its source must remain unchanged.

## Architecture
1. Browser captures or uploads a KTP image.
2. Laravel stores the image on private local storage only.
3. Laravel sends the image to an offline OCR service.
4. OCR returns raw text and parsed KTP fields with confidence where available.
5. Laravel renders editable fields for operator review.
6. Operator explicitly confirms the data.
7. A narrowly scoped SIPP writer/stored procedure persists only approved fields.
8. Every SIPP write is audit logged.

## Initial KTP fields
- NIK
- Nama
- Tempat lahir
- Tanggal lahir
- Jenis kelamin
- Alamat
- RT/RW
- Kelurahan/Desa
- Kecamatan
- Agama
- Status perkawinan
- Pekerjaan
- Kewarganegaraan
- Berlaku hingga
- Raw OCR text

Only fields actually required by the target SIPP entity should be written to SIPP.

## Security rules
- Never expose KTP images under `public/`.
- Never store KTP images in Git.
- Never send KTP images to third-party OCR services.
- Never write OCR results directly to SIPP without human review.
- Use a dedicated DB service account or SQL SECURITY DEFINER stored procedure with least privilege.
- Log actor userid, case/perkara id, sidang id, timestamp, changed fields, target record id and result.
- Do not log the full NIK or full OCR payload in application logs.
- Validate image type, size and dimensions.
- Reject executable/polyglot uploads.
- Use CSRF protection and the existing BAS-AI authentication middleware.

## Phase 1
- Audit the cloned Livewire component and capture schema.
- Add the KTP module UI above audio upload in `/basai/test`.
- Implement camera/file acquisition.
- Store capture privately.
- Implement OCR adapter interface.
- Audit whether an offline OCR engine already exists on .95 or .81.
- Do not change SIPP yet.

## Phase 2
- Implement offline OCR on the selected host.
- Parse Indonesian KTP fields.
- Show editable review form and raw OCR text.
- Add confidence/warning indicators.

## Phase 3
- Audit the live SIPP schema for the intended target entity.
- Define exact field mapping.
- Create least-privilege write path.
- Add explicit operator confirmation.
- Add audit trail and rollback-safe write behavior.

## Acceptance criteria
- Main team page remains unchanged.
- `/basai/test` contains a KTP module above audio upload.
- KTP image is private and inaccessible by direct public URL.
- OCR text and parsed fields appear in the UI.
- Operator can edit before submission.
- No SIPP write occurs before explicit confirmation.
- All writes are auditable.
