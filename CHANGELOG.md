# Changelog

## 2026-11-13 — Laravel BASAI_TES to GPU authenticated readiness (operator-provided)
- Temporary Laravel 13 `basai_tes` installed on `192.168.16.95` at `/var/www/html/basai_tes`, with Apache Alias pointing to the application's `public` directory. Existing Laravel sites were kept separate.
- Verified HTTP `/basai_tes/` returns 200, while `.env`, `composer.json`, and controller source test URLs return 404 after adding `RewriteBase /basai_tes/` in that app's `.htaccess`.
- Validated PHP syntax for `config/basai.php`, `GpuIntegrationException`, `GpuSttClient` and `BasaiGpuStatus`.
- Verified a temporary SSH local forward `192.168.16.95:127.0.0.1:18166` to `192.168.16.81:127.0.0.1:18066` returns `{"status":"alive"}`.
- `php artisan basai:gpu-status` returned `BAS-AI GPU: CONNECTED`, `CUDA: cuda_available`, `Model loaded: YES`.
- Observed that the temporary tunnel can disappear when the SSH session ends. **Persistent systemd tunnel has not yet been deployed.**
- This is a development integration only; no Laravel-to-GPU upload job, durable queue, or end-to-end case transcription through Laravel has been accepted.

## 2026-11-12 — STT production cutover and CUDA inference validated (operator-provided)
- Prepared `/opt/basai-stt` with the reviewed GitHub Compose and protected local `.env`; host-side `docker compose config --quiet` passed.
- Activated container `basai-stt` from existing image `sha256:bb4317edd325b0366384660f37a3f182a19a5a12757c2bb8031b3c8adec78c25`, without rebuilding.
- Observed `Status=running`, `Health=healthy`, `Restart=unless-stopped`, and `GET /health/live` returned `{"status":"alive"}`.
- Preserved original STT container `basai-stt-stage66-basai-stt-1` stopped and Ollama `bas-ollama` running.
- Authorized `GET /health/ready` returned `{"status":"cuda_available","model_loaded":"false"}` prior to the first inference (model is loaded lazily).
- Authorized `POST /v1/stt/transcribe` returned `status=NEEDS_REVIEW`, `model=turbo`, `device=cuda`, **8 segments**, `processing_seconds=7.263`, and the test script reported `STT INFERENCE: PASS`.
- **Acceptance scope:** confirmed liveness, CUDA readiness and one real inference. Not yet verified: automatic recovery after Docker/host restart, long-running stability, sustained concurrent traffic, Laravel connectivity, or accuracy of courtroom transcription.

## 2026-11-12 — GPU host preflight rechecked (operator-provided)
- Confirmed existing local image `basai-stt:6.6.0`: `sha256:bb4317edd325b0366384660f37a3f182a19a5a12757c2bb8031b3c8adec78c25`.
- Confirmed existing model volume: `basai-stt-stage66_basai_models`, mountpoint `/data/docker/volumes/basai-stt-stage66_basai_models/_data`.
- Observed legacy STT container: `Exited (255)`; observed Ollama container: running.
- **No deployment executed and no model or container data modified** by this verification.

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
- Verify automatic recovery after a controlled Docker/host restart **only in an approved maintenance window**.
- Complete secure Laravel 13-to-GPU network transport; current GPU STT binding is `127.0.0.1:18066`.
- Implement reliable Laravel queueing, timeouts and failure handling for one-GPU-at-a-time inference.
- Define safe handling for recordings longer than 600 seconds and judge-reviewed transcripts.
- Create a separately tagged and tested application image for any Python source changes.
- Standardize Ollama only after the STT integration is accepted.
