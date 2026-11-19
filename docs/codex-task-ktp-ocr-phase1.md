# Codex Task — KTP OCR Phase 1 on Laravel .95

Work in: `/var/www/html/basai_tes`

## Goal
Add a KTP capture module to the isolated sandbox page `/basai/test`, positioned above the existing audio upload/recording module.

## Hard boundaries
Read-only reference only:
- `app/Livewire/BasAiAssistant.php`
- `resources/views/livewire/bas-ai-assistant.blade.php`
- `resources/views/components/layouts/app.blade.php`

Allowed modification scope:
- `app/Livewire/BasAiTestAssistant.php`
- `resources/views/livewire/bas-ai-test-assistant.blade.php`
- new BAS-AI test-only services/classes
- tests
- docs

Do not modify:
- `.env`
- Apache/systemd/firewall
- production/team page source
- SIPP data

## First actions — audit only
1. Inspect the cloned Livewire test component and exact Blade structure.
2. Locate the audio upload section so the KTP module can be inserted immediately above it.
3. Inspect existing `basai_captures` migration/schema/model and any capture service.
4. Audit whether Tesseract, PaddleOCR, Python OCR packages, or an existing OCR HTTP service are already available on .95 or configured for .81.
5. Inspect current storage disk configuration without printing secrets.
6. Audit SIPP schema only through existing safe/read paths to identify likely target entity/table for witness identity. Do not write anything.
7. Report exact file:line findings before editing.

## Phase 1 implementation after audit
Add a panel titled `Ambil Data KTP Saksi` above audio upload with:
- camera/file mode
- `Buka Kamera`
- `Ambil Foto`
- `Pilih Gambar KTP`
- image preview
- `Baca KTP`
- OCR status
- editable fields:
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
- collapsible raw OCR text
- disabled/inactive `Submit ke SIPP` until exact schema mapping is approved

## Storage/security
- KTP images must be stored on private Laravel storage, never `public/`.
- Use MIME + content validation.
- Max file size must be explicit.
- Do not log full NIK or raw OCR text.
- Do not send image to any external third-party service.
- Keep original image immutable; derived/preprocessed images must be separate.
- Associate capture with authenticated BAS-AI userid and available perkara/sidang identifiers.
- CSRF/auth middleware must remain active.

## OCR adapter
Create a clean interface/service boundary so OCR backend can later be:
- local CLI/process, or
- private GPU HTTP service.

Do not hard-code a third-party API.

## Validation
Before completion:
- PHP lint relevant files
- relevant Laravel tests
- route remains protected
- `/basai/test` renders
- existing audio module still renders
- git diff shown
- no team-owned source changed

Stop and ask before:
- installing OS packages
- using sudo
- changing database privileges
- writing to SIPP
