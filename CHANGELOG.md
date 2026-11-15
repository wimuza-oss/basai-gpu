# Changelog

Semua perubahan penting proyek BAS-AI GPU dan integrasi Laravel dicatat di file ini.

## [Unreleased]

### Added
- Dokumen kontrak integrasi Laravel 13 dan persyaratan WAJIB pipeline audio.
- Skrip audit read-only untuk `/var/www/html/basai_tes`.
- Aturan diagnosis konfigurasi melalui bootstrap Laravel untuk mencegah false diagnosis dari skrip standalone.
- Runbook operasional restart/reconnect untuk Laravel dan SSH tunnel GPU.
- Izin penggunaan halaman uji upload/recording khusus `basai_tes` untuk menguji pipeline end-to-end.

### Fixed / Verified
- HTTP `/basai_tes` pulih menjadi 200.
- `.env` dipastikan dapat dibaca dan `APP_KEY` lama dipertahankan.
- Permission `.env` disetel terbatas untuk owner dan group web.
- `basai-gpu-tunnel.service` terverifikasi `enabled`, `active`, `Restart=always`, dan restart delay 10 detik.
- Listener `127.0.0.1:18167` terverifikasi LISTEN oleh proses SSH.
- Tunnel berjalan stabil dengan `Result=success`, `SubState=running`, dan tanpa reconnect loop pada journal saat pemeriksaan.

### Root cause identified
- `config/basai.php` menempatkan `pipeline` di bawah `gpu`, sehingga Laravel membentuk `basai.gpu.pipeline` sementara service membaca `basai.pipeline.*`.
- Perbaikan yang disetujui: pindahkan hanya blok `pipeline` ke level top-level `basai`; jangan mengubah konfigurasi GPU yang telah lulus.

### Fixed / Verified
- `config/basai.php` diperbaiki dari `basai.gpu.pipeline` menjadi top-level `basai.pipeline`.
- `config('basai.pipeline')` terverifikasi sebagai array.
- `config('basai.pipeline.source_disks')` terverifikasi berisi `basai_originals`.
- `LaravelDiskAudioSource` kini menerima disk `basai_originals` melalui allowlist konfigurasi.
- HTTP `/basai_tes` tetap 200 setelah patch konfigurasi.

### Current known issues
- FFmpeg belum ditemukan di PATH pada audit terakhir.

### Verified baseline
- Laravel 13.42.0.
- PHP 8.3.36.
- GPU host `192.168.16.81`.
- `basai:gpu-status` sebelumnya telah lulus: CONNECTED, CUDA available, model loaded.


### Pipeline architecture audit
- `LaravelDiskAudioSource` memvalidasi disk melalui allowlist `basai.pipeline.source_disks` dan menolak absolute path, backslash, NUL, serta traversal `.` / `..`.
- `AudioStager` membuat temporary local copy pada work directory, membatasi ukuran sumber, menghitung SHA-256, memverifikasi optional expected checksum, dan selalu cleanup melalui `finally`.
- Laravel Process facade dan Symfony Process tersedia; implementasi FFmpeg dapat memakai process API tanpa shell concatenation.
- Belum ditemukan route/controller BAS-AI pada audit terakhir.
- Belum ditemukan class normalizer FFmpeg pada audit terakhir.
- Kontrak metode transkripsi pada `GpuSttClient` masih perlu dibaca sebelum membuat test UI agar tidak membuat jalur integrasi paralel.


### GPU transcription contract recovered
- Endpoint transkripsi GPU yang pernah diuji sebelumnya: `POST /v1/stt/transcribe`.
- Request: multipart/form-data field `file`, tipe audio WAV.
- Authentication: header `X-BASAI-Key`.
- Laravel mengakses endpoint tersebut melalui tunnel lokal `127.0.0.1:18167`.
- Respons sukses memuat metadata status/language/model/device/processing_seconds dan `segments[]`.
- Dengan kontrak ini, tidak diperlukan audit tambahan untuk mencari endpoint GPU.
- Sisa verifikasi dibatasi menjadi tiga gerbang: FFmpeg, satu E2E WAV->GPU, satu UI upload/recording.


### Approved host dependency
- 2026-11-13: pemasangan paket OS `ffmpeg` pada host Laravel `192.168.16.95` disetujui karena merupakan dependency wajib untuk normalisasi audio sebelum transkripsi GPU.
- Paket target dari Ubuntu 22.04 repositories: `7:4.4.2-0ubuntu0.22.04.1`.
- Setelah instalasi, verifikasi dibatasi pada satu pengecekan executable/version lalu implementasi `FfmpegAudioNormalizer`.


### FFmpeg verified
- Host Laravel `192.168.16.95` memiliki `/usr/bin/ffmpeg` dan `/usr/bin/ffprobe`.
- Versi terverifikasi: `4.4.2-0ubuntu0.22.04.1`.
- Gerbang verifikasi FFmpeg dinyatakan selesai; tidak perlu diuji ulang tanpa perubahan dependency.


### FFmpeg normalizer implemented
- `FfmpegAudioNormalizer` telah ditambahkan pada Laravel `basai_tes`.
- Syntax PHP lulus.
- Konfigurasi runtime terverifikasi:
  - ffmpeg: `/usr/bin/ffmpeg`
  - ffprobe: `/usr/bin/ffprobe`
  - timeout: `180`
- Normalizer menggunakan Symfony Process dengan argument array, bukan shell command concatenation.
- Output contract: WAV / pcm_s16le / 16 kHz / mono, diverifikasi kembali melalui FFprobe.
- Temporary output dibersihkan melalui `finally`.


### Recording config nesting issue identified
- `RecordingStorageService` membaca `config('basai.recordings.originals_root')`.
- `config/basai.php` masih menempatkan `recordings` di bawah `gpu`, sehingga key runtime yang tersedia adalah `basai.gpu.recordings`.
- Sebelum UI test dibuat, blok `recordings` harus dipindahkan ke top-level `basai.recordings`, sama seperti perbaikan `pipeline`.
- Patch ini akan digabung dengan implementasi halaman test agar tidak menambah siklus audit terpisah.


### Laravel CLI compatibility note
- Laravel 13.42.0 pada host sementara tidak mendukung opsi `php artisan route:list --columns=...`.
- Gunakan `php artisan route:list --path=basai/test` tanpa `--columns`.
- Syntax modul test dan konfigurasi `basai.recordings` / `basai.pipeline` sudah lulus; kegagalan opsi CLI ini bukan kegagalan aplikasi.


### First E2E upload test
- Upload WAV melalui halaman `/basai/test` berhasil mencapai controller, tetapi pipeline mengembalikan pesan generik `Transkripsi gagal. Periksa log BAS-AI.`.
- Root cause belum ditetapkan; next action adalah membaca exception terbaru pada `storage/logs/laravel.log` tanpa mengulang test.
- Jangan mengulang GPU readiness, tunnel, FFmpeg install, atau konfigurasi pipeline yang sudah lulus.


### Audio input format policy
- Input pengguna tidak harus WAV.
- Format input target: WAV, MP3, dan WebM.
- Semua input dinormalisasi secara internal oleh FFmpeg menjadi WAV / PCM signed 16-bit little-endian / 16 kHz / mono sebelum dikirim ke Whisper.
- Konversi MP3 ke WAV tidak meningkatkan kualitas sumber yang sudah lossy; WAV hanya menjadi format internal standar untuk inference.
- Kegagalan E2E pertama bukan disebabkan format WAV. Request telah melewati storage, staging, FFmpeg, dan mencapai GPU; parser Laravel menolak struktur salah satu item `segments` dari respons GPU.


### Fixed GPU segment contract
- Root cause E2E failure: Laravel `GpuSttClient` expected `segments[].text`, while the GPU transcription service returns segment text in `segments[].raw_text`.
- Parser must accept `raw_text` as the primary field and `text` as a compatibility fallback.
- No changes required to tunnel, FFmpeg, Apache, or GPU Docker.


### End-to-end transcription verified
- 2026-11-13: uji upload WAV melalui `/basai/test` berhasil penuh.
- Pipeline yang terbukti bekerja:
  `RecordingStorageService -> LaravelDiskAudioSource -> AudioStager -> FfmpegAudioNormalizer -> GpuSttClient -> Whisper GPU -> Laravel UI`.
- Input test: WAV.
- Original bytes: 324942.
- Normalized bytes: 216654.
- Normalized format: `pcm_s16le`, 16000 Hz, mono.
- GPU model: `turbo`.
- GPU device: `cuda`.
- Language: `id`.
- Processing time: 0.266 seconds.
- Segments: 2.
- GPU status: `NEEDS_REVIEW`.
- Transcript returned successfully to the Laravel page.
- `NEEDS_REVIEW` is treated as a model/result review state, not a transport or pipeline failure.


### Checkpoint: single-stream E2E complete
- Checkpoint 2026-11-13: integrasi Laravel 13 -> FFmpeg -> GPU Whisper -> transcript UI dinyatakan berhasil dan dihentikan sementara pada titik ini.
- Tahap berikutnya yang direncanakan: speaker diarization dan role mapping untuk memisahkan ucapan Hakim, Penggugat, Tergugat, Saksi 1, Saksi 2, dan peran lain.
- Gender suara tidak boleh dijadikan identitas hukum/peran. Role harus dipetakan dari konteks sidang, channel/microphone, atau assignment eksplisit.
- Target output masa depan:
  - Hakim: pertanyaan...
  - Saksi 1: jawaban...
  - Hakim: pertanyaan...
  - Penggugat: jawaban...


### Hybrid channel identity + diarization design
- Arsitektur speaker identification ditetapkan sebagai hybrid: channel identity + per-channel speaker diarization.
- 4-channel baseline mendukung shared witness channel untuk Saksi 1/Saksi 2.
- 8-channel baseline disiapkan tanpa perubahan schema inti.
- Role mapping wajib configurable per sidang; channel number tidak di-hard-code sebagai identitas hukum.
- Canonical data tetap ordered speaker turns; format Tanya/Jawab merupakan derived view.
- Crosstalk/microphone bleed harus ditangani dengan channel dominance + diarization evidence + confidence/NEEDS_REVIEW.
- Detail desain: `docs/SPEAKER_DIARIZATION_ARCHITECTURE.md`.


### D1 diarization GPU audit: PASS
- GPU host: Ubuntu 26.04.1 LTS, kernel 7.0.0-43.
- GPU: NVIDIA GeForce RTX 5060 Ti 16 GB.
- Driver 595.99.02; CUDA driver capability 13.2.
- STT active GPU usage: ~1210 MiB; free VRAM ~14641 MiB.
- System RAM available ~26 GiB; swap unused.
- /data available ~1.4 TiB.
- Existing basai-stt:6.6.0 healthy on 127.0.0.1:18066.
- Port 18067 selected for isolated basai-diarization service.
- bas-ollama container is running but no separate GPU compute process was observed during D1.
- D2 decision: keep diarization in a separate container and preserve basai-stt unchanged.


### D2A diarization model offline: PASS
- Model `pyannote/speaker-diarization-community-1` berhasil diunduh pada 2026-11-13.
- Local path: `/data/stt/diarization-models/community-1`.
- Download completed: 10/10 files.
- Offline model size: ~33 MiB.
- Runtime diarization tidak memerlukan Hugging Face token.
- Token tidak disimpan ke GitHub/image/runtime config.


### D2B deploy-key authentication: PASS
- GPU host authenticated successfully to private repository `wimuza-oss/basai-gpu` using a dedicated SSH deploy key.
- Deploy key is read-only; GitHub shell access is intentionally unavailable.
- GPU host is ready to clone the repository as the deployment source of truth.


### D2B repository clone: PASS
- GPU host successfully cloned private repository `wimuza-oss/basai-gpu` to `/opt/bas-ai/basai-gpu`.
- Branch: `main`.
- Working tree: clean.
- Deployment source `services/diarization` is present and ready for build.


### D2B isolated diarization service: PASS
- Image `basai-diarization:1.0.0` built successfully.
- Container `basai-diarization` started on `127.0.0.1:18067->8000/tcp`.
- `GET /health/ready` returned CUDA-ready with model `community-1`.
- GPU device: NVIDIA GeForce RTX 5060 Ti.
- Additional diarization GPU memory observed: ~212 MiB.
- Existing `basai-stt` remained running at ~1196 MiB VRAM.
- No change made to the stable STT container.


### D3 two-speaker single-channel diarization: PASS
- One mono/shared-channel WAV containing two speakers was processed successfully.
- Engine: pyannote Community-1 on CUDA.
- Processing time: 0.594 s.
- Detected speakers: 2.
- SPEAKER_00: 31 ms - 3440 ms.
- SPEAKER_01: 3710 ms - 6680 ms.
- Gap between turns: ~270 ms.
- Exclusive diarization and regular speaker activity agreed for this sample.
- This validates the shared-channel strategy for Saksi 1 / Saksi 2 or other role pairs.


### D4 Laravel UI baseline: STT-only confirmed
- Browser upload at `/basai/test` still returns the existing STT-only result.
- Whisper E2E remains healthy: model `turbo`, CUDA, Indonesian language, 2 segments, processing ~0.275 s.
- No speaker labels are rendered yet; diarization is not yet integrated into Laravel.
- D4 remains **NOT PASS** until browser upload invokes diarization, aligns timestamps, and renders speaker-labeled transcript.


### D4 diarization SSH tunnel: PASS
- Laravel host successfully reaches diarization through a dedicated SSH tunnel.
- Local mapping: `127.0.0.1:18168 -> GPU 127.0.0.1:18067`.
- GPU readiness returned `cuda_available`, model `community-1`, device `cuda`.
- SSH authorized_keys policy now explicitly permits both `127.0.0.1:18066` (STT) and `127.0.0.1:18067` (diarization).
- STT tunnel remains isolated on `127.0.0.1:18167`.


### D4 Laravel UI diarization E2E: PASS
- Browser upload through `/basai/test` successfully executed the full application path.
- Whisper transcript:
  - `Saudara saksi, apakah saudara kenal dengan penggugat?`
  - `Kenal yang mulia, saya kakak kandungnya.`
- Speaker alignment result:
  - SPEAKER_00: 0.00s - 3.38s, confidence 0.991.
  - SPEAKER_01: 3.74s - 6.56s, confidence 1.000.
- Whisper processing time: ~0.264 s.
- Model: turbo; device: CUDA; language: id; STT segments: 2.
- D4 acceptance criteria fulfilled: one browser upload produced speaker-labeled transcript in Laravel UI.
- Next phase: per-session role mapping, e.g. SPEAKER_00 -> HAKIM and SPEAKER_01 -> SAKSI_1.


### D5 admin settings and role mapping design
- BAS-AI global settings will live under the existing Admin/Settings area.
- Global configuration includes role catalog, channel profiles, diarization policy, STT policy, satker identity, device settings, and integration settings.
- Diarization IDs such as `SPEAKER_00` are **not global configuration**; they are mapped to legal roles per hearing/session.
- Session mapping and admin settings use separate authorization.
- Details: `docs/ADMIN_SETTINGS_ROLE_MAPPING.md`.


### D5 database target confirmed
- Existing MariaDB database `basai` on `192.168.16.121` is the target persistence store for BAS-AI settings, hearing sessions, channel profiles, and speaker-role mappings.
- Do not create a second BAS-AI database.
- D5 implementation must audit existing schema first and add only non-conflicting tables/migrations.
- Application credentials remain least-privilege; DML is limited to the `basai` schema.


### D5 Laravel database connection mismatch identified
- Laravel test application was still configured with the default `sqlite` connection.
- Active database path was `/var/www/html/basai_tes/database/database.sqlite`, which does not exist.
- This is a Laravel configuration mismatch, not a failure of MariaDB `basai`.
- Target remains the existing MariaDB database `basai` on `192.168.16.121:3306`.
- Next action: switch Laravel connection to MariaDB using the team's existing database credentials; do not create a new database.


### D5 database credentials missing on Laravel host
- Laravel host `192.168.16.95` is now configured for `mysql` / `192.168.16.121` / database `basai`.
- `DB_USERNAME` and `DB_PASSWORD` are not yet provisioned in the Laravel environment.
- No credentials are stored in GitHub.
- Do not reuse root/admin credentials or an account bound to another host.
- Next action: read-only audit of MariaDB accounts for host `192.168.16.95`; create a dedicated least-privilege account only if none exists.


### D5 MariaDB account migration plan
- Existing account `basai_app@192.168.16.86` belongs to the retired BAS-AI controller host.
- New Laravel host is `192.168.16.95`.
- Preferred action: audit grants, then rename the MariaDB account host from `192.168.16.86` to `192.168.16.95` so password hash and grants are preserved.
- Do not reuse `basai@%` or root/admin accounts.


### D5 runtime database grants audited
- Existing `basai_app@192.168.16.86` has only:
  - `USAGE` globally;
  - `SELECT, INSERT, UPDATE, DELETE` on `basai.*`.
- Grants are appropriate for Laravel runtime and should be preserved when renaming the host binding to `192.168.16.95`.
- Runtime account intentionally has no DDL privileges. Laravel schema migrations must use a separate migrator/admin credential.
- Credential hashes/passwords are not recorded in repository documentation.


### D5 MariaDB runtime authentication mismatch
- After moving the runtime account binding to `basai_app@192.168.16.95`, Laravel reached MariaDB `192.168.16.121:3306` but authentication failed with SQLSTATE 1045.
- Host binding is therefore aligned; the remaining issue is the runtime password/credential value.
- Resolution policy: reset the dedicated `basai_app@192.168.16.95` password and update only the Laravel host environment. Do not use root/admin credentials in the application.


### D5 direct MariaDB login also fails
- Direct TCP login from Laravel host 192.168.16.95 to MariaDB 192.168.16.121 as basai_app also returns SQLSTATE/ERROR 1045.
- Therefore the current failure is at the MariaDB account/authentication layer, not Laravel config/cache.
- Next action: inspect authentication plugin for basai_app@192.168.16.95 and reset that account explicitly while preserving least-privilege grants.


### D5 Laravel MariaDB runtime connection: PASS
- Laravel host 192.168.16.95 successfully connects to MariaDB 192.168.16.121.
- Active database: `basai`.
- Authenticated account: `basai_app@192.168.16.95`.
- Database version: MariaDB 10.6.19-log.
- Runtime account remains least-privilege with DML-only access on `basai.*`.


### D5 Laravel database via ProxySQL: PASS
- Laravel database connection has been moved from direct MariaDB backend access to ProxySQL.
- ProxySQL endpoint: `192.168.16.236:6033`.
- Target schema remains `basai`.
- Connection test is reported successful.
- This is the preferred application path for production-style database access; direct backend `192.168.16.121:3306` remains an infrastructure/backend concern rather than the normal Laravel runtime endpoint.


### D5A existing schema inventory
- Laravel via ProxySQL successfully reaches database `basai`.
- Existing tables:
  - `alembic_version`
  - `basai_captures`
  - `basai_hearing_completions`
  - `jobs`
- No Laravel `migrations` table exists yet.
- Existing BAS-AI schema is therefore inherited from the prior Alembic/FastAPI phase.
- Existing tables must be preserved; D5 will add Laravel-owned settings/role/channel/session mapping schema without destructive changes.


### D5 schema simplified after legacy inspection
- Existing `basai_captures` and `basai_hearing_completions` already establish `hearing_id` + `case_id` as the hearing identity contract.
- D5 will not create a redundant `basai_hearing_sessions` table.
- Speaker mappings will be scoped directly to `hearing_id` + `case_id`.
- No legacy tables or Alembic metadata will be modified.


### D5 authorization boundary clarified
- Laravel application Admin privileges are separate from MariaDB DDL privileges.
- Admin users may manage BAS-AI settings through Laravel authorization while the application continues using the least-privilege runtime account `basai_app`.
- Schema changes are an operational/deployment concern, not a capability granted to Laravel Admin users.
- User authorization granted for schema/data changes **only inside database `basai`**. Other databases/schemas must not be modified.
- Laravel migrations remain useful for versioning and rollback documentation, but are not a prerequisite for the Admin UI itself.


### D5B schema SQL prepared
- Added idempotent MariaDB DDL/seed script at `database/sql/001_d5_admin_settings.sql`.
- Scope is explicitly `USE basai`.
- Adds six Laravel/D5 tables without modifying legacy Alembic tables.
- Seeds role catalog, 4-channel profile, 8-channel profile, and safe non-secret settings defaults.
- Runtime secrets are not stored in `basai_settings`.


### D5C Bahasa Indonesia schema naming prepared
- Domain table and column names are standardized to Bahasa Indonesia.
- `case_id` is renamed to `perkara_id` to align with SIPP terminology.
- `hearing_id` is renamed to `sidang_id`.
- Framework/metadata tables `alembic_version` and `jobs` remain unchanged.
- Forward SQL: `database/sql/002_indonesianize_basai_schema.sql`.
- Rollback SQL: `database/sql/002_indonesianize_basai_schema.rollback.sql`.


### D5C schema naming corrected to project convention
- D5C SQL updated to follow the project naming guide exactly.
- Uses `basai_sidang_sidang`, `basai_setting`, `basai_profil_channel`, `basai_detail_profil_channel`, and `basai_pembicara`.
- Uses `perkara_id`, `sidang_id`, `jumlah_channel`, `nomor_channel`, and `nama_channel`.
- `setting_group` and `setting_key` remain unchanged.
- `owner_id` is finalized as `userid`, referring to the authenticated SIPP/BAS user identity.


### D5C owner identity finalized
- `owner_id` is renamed to `userid`.
- `userid` represents the authenticated SIPP/BAS user identity for the media/capture record.
- BAS-AI does not create a duplicate user identity and does not add a cross-database foreign key to the SIPP/BAS user table.


### D5C Indonesian schema rename: PASS
- Database `basai` now uses the approved BAS-AI domain table naming convention.
- Confirmed tables:
  - `basai_audit_pengaturan`
  - `basai_detail_profil_channel`
  - `basai_media_sidang`
  - `basai_pembicara`
  - `basai_peran`
  - `basai_profil_channel`
  - `basai_setting`
  - `basai_sidang_sidang`
- Framework/metadata tables `alembic_version` and `jobs` remain unchanged.
- Next phase: update Laravel code references from legacy English schema names/columns to the approved schema.


### D5C Laravel legacy-schema reference scan: PASS
- Read-only scan of Laravel `app`, `config`, `routes`, `resources`, and `database` found no references to the pre-D5C English BAS-AI table/column names.
- The database rename therefore does not require a compatibility patch for existing Laravel code.
- D5D can implement the Admin settings module directly against the approved Indonesian schema.


### D5D authentication source finalized
- BAS-AI will authenticate against SIPP/BAS `sys_users`.
- `/basai/test` will require the same SIPP/BAS user identity instead of a separate BAS-AI account.
- SIPP/BAS administrator identity will govern BAS-AI administrator access.
- BAS-AI will not duplicate passwords or user records.


### D5D SIPP sys_users contract confirmed
- Confirmed `soreang.sys_users.userid` as the canonical BAS-AI authenticated user identity.
- `sys_users` has no direct admin flag; administrative access must follow SIPP group/rule authorization.
- Password algorithm remains intentionally unassumed pending inspection of the existing BAS/SIPP login implementation.


### D5D BAS authentication source scan
- Source scan under the legacy BAS application did not find normal login/session/user authorization references.
- The only authentication-related match was the standalone read-only `basai-catalog.php`, which is not evidence of the BAS application's primary authentication flow.
- Authentication may therefore be enforced outside ordinary BAS application controllers (bootstrap/hooks/web server/upstream integration); this must be confirmed before reproducing it in Laravel.


### D5D authentication deployment architecture finalized
- Apache configuration shows proxy/access rules only; no upstream authentication mechanism was found for legacy BAS.
- BAS-AI Laravel will own its login form/session while authenticating against read-only SIPP `sys_users`.
- BAS-AI administrator authorization will follow SIPP group/rule membership.


### D5D SIPP administrator group identified
- `sys_groups.groupid=1` is enabled `Super Administrator`.
- `sys_groups.groupid=2` is named `Administrator` but disabled, so it must not be treated as an active BAS-AI admin source.
- Final admin predicate awaits only the exact `sys_user_group` membership columns.


### D5D admin predicate finalized
- Confirmed `sys_user_group(userid, groupid)` as the SIPP user-to-group membership table.
- BAS-AI admin access is membership in enabled SIPP `Super Administrator` group `groupid=1`.
- SIPP authorization tables remain read-only from BAS-AI.


### D5D login eligibility finalized
- SIPP password format confirmed as legacy 32-character hexadecimal MD5-compatible hashes.
- BAS-AI login is restricted to enabled Super Administrator users and enabled users in the Panitera hierarchy rooted at `groupid=30`.
- Panitera descendants are included through SIPP nested-set `lft/rgt`; this includes Panitera Pengganti (`groupid=500`).
- Super Administrator remains the BAS-AI Admin role; Panitera hierarchy users are operational users by default.


### D5D login allowlist corrected
- Removed subtree-based Panitera authorization because it incorrectly includes Jurusita and other descendants.
- BAS-AI login now uses an explicit role allowlist: Super Administrator, Panitera/Wakil Panitera, enabled Panmud/Panitera Muda groups, and Panitera Pengganti.
- Jurusita is explicitly excluded.
- Super Administrator remains BAS-AI Admin; the other allowed roles are operational users.


### D5E least-privilege SIPP authentication gateway prepared
- Direct runtime SELECT from `basai_app` to `soreang.sys_users`, `sys_user_group`, and `sys_groups` is denied, preserving isolation.
- Added `basai.basai_autentikasi_sipp` as a `SQL SECURITY DEFINER` authentication gateway.
- Laravel receives only userid, fullname, username, and admin_basai; stored SIPP password hashes are not exposed.
- Runtime permission is limited to EXECUTE on the BAS-AI procedure through `basai_app@192.168.16.236`.
- No SIPP table or SIPP data is modified.


### D5E Laravel SIPP authentication service prepared
- Added `SippUserData`, `SippAuthenticationException`, and `SippAuthenticationService` reference implementation.
- Service calls `basai.basai_autentikasi_sipp` only; it never queries `soreang.sys_*` directly.
- Legacy SIPP password verification uses MD5 only for compatibility with the existing SIPP contract.
- MariaDB procedure result sets are explicitly drained/closed to keep the PDO connection reusable.


### D5E ProxySQL runtime path: PASS
- Laravel runtime connection successfully uses ProxySQL `192.168.16.236:6033`.
- ProxySQL has separate frontend and backend entries for `basai_app`.
- MariaDB backend sees the authenticated account as `basai_app@192.168.16.236`.
- Active database is `basai`.
- The previous frontend credential mismatch has been resolved.


### D5F SIPP login/session UI prepared
- SIPP authentication gateway probe returned `null` for invalid credentials: end-to-end gateway PASS.
- Added validated BAS-AI login request.
- Added SIPP login/logout controller with session regeneration/invalidation.
- Session stores only userid, username, fullname, and admin_basai.
- Added CSRF-protected BAS-AI login Blade view.
- Password/hash is never stored in the Laravel session.


### D5F route-name decoupling
- SIPP login controller redirects directly to `/basai/test` and no longer assumes the existing test route is named `basai.test`.


### D5G SIPP password algorithm correction
- Root cause identified from legacy SIPP source: authentication does not compare sys_users.password with md5(password) directly.
- SIPP computes arr2md5([code_activation, password]): md5(code_activation) XOR md5(password), then md5() of the XOR result.
- Added basai_hash_password_sipp() in database basai and updated basai_autentikasi_sipp() to reproduce the legacy algorithm.
- Laravel continues to send only md5(password) to the gateway; plaintext password is not sent to MariaDB.
- Expanded explicit known Panitera/Panmud group IDs from the legacy source while retaining dynamic Panmud matching.


### D5G.1 legacy collation compatibility
- Fixed MariaDB error 1267 caused by comparing legacy SIPP latin1_swedish_ci columns with BAS-AI utf8mb4_unicode_ci procedure parameters.
- Username comparison now explicitly converts the SIPP value to utf8mb4 and preserves case-insensitive matching.
- Password hashes are compared as binary ASCII values, avoiding collation-dependent comparison.
- code_activation is explicitly converted to utf8mb4 before the SIPP hash function is evaluated.


### D5G.2 end-to-end login and STT PASS
- Real SIPP Panitera Pengganti account successfully authenticated through Laravel -> ProxySQL -> basai_autentikasi_sipp().
- BAS-AI login session was established successfully.
- Authenticated user successfully uploaded a WAV file from the Laravel BAS-AI test page.
- GPU STT processing completed successfully and transcription was returned to Laravel.
- This validates the end-to-end path: SIPP identity -> Laravel session -> WAV upload -> GPU STT -> transcript.


### D5H route protection and authenticated identity
- Added RequireBasaiAuthentication middleware for the BAS-AI session namespace.
- Invalid/missing session is cleared and redirected to basai.login with intended URL retained.
- Middleware exposes only normalized userid, username, fullname, and admin_basai to the request/view.
- Added authenticated user bar Blade partial with CSRF-protected POST logout.
- Existing STT controller and GPU pipeline are intentionally unchanged.
- Route/view integration is documented separately because the live team-owned routes/web.php and BAS-AI test Blade are not yet mirrored in this repository.


### D5H installer
- Added fail-safe installer for the live Laravel tree.
- Installer requires exactly one basai.test.show and basai.test.transcribe named route, discovers the test Blade from BasaiTestController, and aborts on unexpected structure.
- routes/web.php and the discovered Blade are backed up before modification.


### D5H.1 verified-live patch
- Replaced the generic D5H route/view patch strategy with a strict patch tailored to the verified live Laravel source.
- Exact live targets: routes named basai.test.show and basai.test.transcribe, and resources/views/basai/test-audio.blade.php.
- Patch aborts unless the exact expected live blocks are present once.
- Backup is created before writing routes/web.php and test-audio.blade.php.
- Login controller, STT controller/service, database and GPU pipeline remain untouched.


### D5H PASS
- BAS-AI SIPP login verified with a real Panitera Pengganti account.
- BAS-AI SIPP login verified with a Super Administrator account.
- Existing authenticated session redirects /basai/login to /basai/test.
- /basai/test is protected by RequireBasaiAuthentication.
- Authenticated identity/logout UI is active on the BAS-AI test page.
- Logout invalidates the BAS-AI session and unauthenticated access is redirected to login.
- Existing WAV upload and GPU transcription pipeline remains operational after D5H.
