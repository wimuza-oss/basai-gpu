# Production Standardization Plan

**Current status:** GitHub STT production Compose prepared. GPU host deployment has not occurred.

## Target state
- STT source directory: `/opt/basai-stt`; Compose project and container: `basai-stt`.
- Local image: `basai-stt:6.6.0` (no pull or build for name-only cutover).
- Model volume: **existing** external `basai-stt-stage66_basai_models`, retained unchanged.
- Localhost API binding: `127.0.0.1:18066:8000`.
- Ollama remains unchanged for now: `/opt/bas-ai/ollama`, container `bas-ollama`, model store `/data/ollama`.

## Execution order
1. Verify existing Docker image, volume and source on GPU host; inspect logs and disk.
2. Prepare `/opt/basai-stt` from reviewed GitHub source with a protected local `.env`.
3. Verify `docker compose config --quiet` and presence of existing image and external model volume.
4. Record rollback procedure, maintenance window and operator authorization.
5. Stop only legacy STT container; start only new STT container, without rebuild, image pull, or volume removal.
6. Confirm liveness, authorized readiness and successful CUDA transcription.
7. Confirm restart policy and uptime recovery without affecting Ollama.
8. Record operational results in change history.
9. Subsequently standardize Ollama to `/opt/basai-llm` with an independently reviewed change.
10. Remove obsolete source directory **only** after successful rollback verification and explicit operator approval.

See [deployment runbook](DEPLOYMENT.md) for commands, precautions and rollback.

## Release limitations
The imported FastAPI source still contains a pilot title and a 600-second recording limit. These should be changed through a separate versioned image release and acceptance testing; editing the Compose alone does not modify Python code inside image 6.6.0.

No production status claim should be made until the GPU host has passed end-to-end tests.
