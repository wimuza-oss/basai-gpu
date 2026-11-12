# Changelog

## 2026-11-12 — Production STT configuration prepared (not deployed)
- Changed tracked `stt/compose.yaml` for production service name `basai-stt`, Compose project `basai-stt`, and pinned local image `basai-stt:6.6.0` with `pull_policy: never`.
- Mapped existing model volume `basai-stt-stage66_basai_models` as external (preserved; not renamed).
- Added `restart: unless-stopped`, init process, shutdown grace period, bounded local logs and healthcheck start period.
- Preserved GPU, non-root image, loopback port exposure, read-only filesystem, tmpfs, dropped capabilities and no-new-privileges.
- Documented operator-only preflight, controlled cutover, acceptance and rollback in `docs/DEPLOYMENT.md`.
- **No GPU host or production container changed.** Image 6.6.0 has not been rebuilt; the code's pilot title remains until a separate vetted release.

## 2026-11-12 — Source import
- Imported 13 files from the supplied STT source archive and added a credential-free example environment file.
- Documented real API paths, authentication and upload constraints from source review.

## 2026-11-12 — Initial GitHub documentation baseline
- Verified private repository `wimuza-oss/basai-gpu` with push access.
- Recorded observed GPU, STT and Ollama inventory, architecture and operations.
- Established data and secret exclusions.

## Pending
- Validate Compose against the actual GPU-host Docker Compose installation, image and volume.
- Apply approved STT cutover and verify CUDA inference and restart behavior.
- Create a separately tagged and tested application image for Python source changes.
- Finalize private authenticated Laravel-to-GPU transport.
- Standardize Ollama only after STT acceptance.
