# GPU Server Inventory

Snapshot: 12 November 2026. Facts are based on server-operator diagnostic output, not a live SSH session.

## Host
- Hostname: gpu; internal address: 192.168.16.81.
- Ubuntu 26.04.1 LTS; RTX 5060 Ti (16,311 MiB); NVIDIA driver 595.99.02.
- Docker service active and enabled; Docker root: /data/docker.
- Storage: approximately 1.4 TB free on /data at the last inspection.

## Whisper STT (observed)
- Compose and source: /opt/basai-stt-stage6.6
- Python entry point: app.main:app; source modules: app/api/routes.py, app/core/config.py, app/core/security.py, app/services/audio.py, app/services/stt.py.
- Image: basai-stt:6.6.0; image SHA256: bb4317edd325b0366384660f37a3f182a19a5a12757c2bb8031b3c8adec78c25.
- Container: basai-stt-stage66-basai-stt-1; at last inspection: Exited (255).
- OOMKilled=false; RestartPolicy=no. Root cause of exit remains unconfirmed.
- Internal port 8000 mapped only to 127.0.0.1:18066.
- Model=turbo; device=cuda; compute_type=int8_float16.
- **Existing model volume: basai-stt-stage66_basai_models**, mounted at /models. DO NOT DELETE.
- Docker healthcheck path: /health/live.

## Ollama (observed)
- Compose: /opt/bas-ai/ollama/compose.yaml; project name: bas-ai.
- Container: bas-ollama; running at last inspection.
- Image: ollama/ollama:latest; model: qwen3.5:9b (reported 6.6 GB).
- Port bound locally: 127.0.0.1:11434.
- Data bind mount: /data/ollama:/root/.ollama. DO NOT DELETE.
- Controls: MAX_LOADED_MODELS=1; NUM_PARALLEL=1; KEEP_ALIVE=5m.

## Not verified
The actual STT request/response contract, security header, current source content, Laravel-to-GPU network path, OCR, diarization, concurrent inference and production accuracy remain unverified.
