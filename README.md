# BAS-AI GPU Inference Services

Private repository for the GPU inference backend of BAS-AI. Laravel 13 is maintained separately by another team.

## Components

- **Speech-to-text:** Faster-Whisper / CTranslate2, CUDA, Python API; image `basai-stt:6.6.0`.
- **LLM:** Ollama with local `qwen3.5:9b` model.
- **Deployment:** Docker Compose with persistent model storage.

## Repository state (12 November 2026)

Documentation baseline only. The current STT service was observed stopped with exit code 255; the new production folder/container names have **not** been deployed. The Python source remains on the GPU host and has not yet been imported here.

## Documentation

- [Server inventory](docs/INVENTORY.md)
- [Architecture](docs/ARCHITECTURE.md)
- [API contract status](docs/API_REFERENCE.md)
- [Operations and recovery](docs/OPERATIONS.md)
- [Production migration plan](docs/MIGRATION_PLAN.md)
- [Change history](CHANGELOG.md)

## Security

Do not commit `.env`, API credentials, case information, audio, KTP images, transcriptions, or model weights. Keep GPU API access private and authenticated.

## Next milestone

Import and review the actual source files from the GPU host, preserve the existing model volumes, then execute an approved, reversible production standardization and validate end-to-end inference.
