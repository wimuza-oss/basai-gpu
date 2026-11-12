# STT API Contract — Verification Pending

Known from the existing Docker Compose:
- ASGI app: app.main:app.
- Container listener: 0.0.0.0:8000.
- GPU host binding: 127.0.0.1:18066.
- GET /health/live is referenced by the Docker healthcheck (response not yet re-verified).
- BASAI_API_KEY is a required Compose setting.
- BASAI_MODEL=turbo; BASAI_DEVICE=cuda; BASAI_COMPUTE_TYPE=int8_float16.

Not yet established: transcription route, HTTP method, upload fields, file limits, request authentication header, error codes, response schema, timeouts, language metadata, OCR routes and LLM routes.

Before finalizing Laravel integration, review actual source files on the GPU server:
- app/api/routes.py
- app/core/security.py
- app/core/config.py
- app/services/stt.py
- app/services/audio.py
- tests/test_api.py

Do not implement clients against guessed endpoint paths.
