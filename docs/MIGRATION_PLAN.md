# Production Standardization Plan

Status: proposed, not executed.

## Target
- STT directory: /opt/basai-stt
- STT container: basai-stt
- LLM config directory: /opt/basai-llm
- LLM container: basai-llm
- Existing Ollama data: /data/ollama
- Existing STT model volume: basai-stt-stage66_basai_models

## Required sequence
1. Preserve the original /opt/basai-stt-stage6.6 directory for rollback.
2. Copy the exact STT source into /opt/basai-stt; do not rewrite source from assumptions.
3. Pin image basai-stt:6.6.0 during the name-only migration.
4. Reference model volume basai-stt-stage66_basai_models as an external volume, rather than allowing a new empty volume to be created.
5. Preserve security: non-root UID, read_only, cap_drop ALL, no-new-privileges, tmpfs, pids_limit and loopback port binding.
6. Review STT restart policy for unless-stopped after confirming failure behavior.
7. Do not move /data/ollama or alter other service data.
8. Confirm authenticated private transport from Laravel before extending port exposure.
9. During approved deployment, verify GPU inference, healthcheck and restart recovery.
10. Keep legacy source and original image until rollback is demonstrably possible.

## Acceptance
- Stable service names, preserved model data and no secret leakage.
- STT health and an authorized real inference both pass.
- No adverse impact to Ollama.
- Rollback evidence recorded.

Current blocker: the actual source files have not been imported into GitHub from the GPU host. This plan alone is not a production deployment.
