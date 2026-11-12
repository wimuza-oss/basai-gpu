# Architecture

## Responsibilities
- Laravel 13 (maintained by another team): user authentication, case data, uploads, orchestration, queue, storage, transcript review and BAS integration.
- GPU STT: authenticated request processing, audio decoding, Faster-Whisper inference, response generation. No direct SIPP/BAS database access required.
- GPU LLM: separate Ollama runtime using local Qwen model; no verified application integration yet.

## Current host paths
- /opt/basai-stt-stage6.6 : current STT source and Compose.
- /opt/bas-ai/ollama : current Ollama Compose.
- /data/ollama : existing Ollama model store.
- /data/docker/volumes/basai-stt-stage66_basai_models/_data : existing STT model data.

## Intended production paths — NOT YET DEPLOYED
- /opt/basai-stt : STT source and Compose; container name basai-stt.
- /opt/basai-llm : Ollama Compose; container name basai-llm.
- Keep the current image basai-stt:6.6.0 until a replacement has been verified.
- Preserve the existing STT model volume by mapping its exact name as an external Compose volume.
- Preserve /data/ollama as the LLM mount source.

## Security
The current STT and LLM host ports intentionally bind only to loopback. Do not publish them publicly for Laravel. Use a private, authenticated network gateway or encrypted tunnel restricted to the Laravel deployment host. Maintain API authentication, non-root execution, read-only filesystems and least-privilege Docker configuration.

## Capacity
Whisper Turbo and Qwen 3.5 9B can compete for one RTX 5060 Ti. Measure VRAM and latency before concurrent workloads.

This repository is a documentation baseline and does not represent a deployed release.
