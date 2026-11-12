# GPU Operations Runbook

Status: documentation only. Commands here were not executed on the GPU server as part of this GitHub change.

## Read-only diagnostics

    sudo systemctl is-active docker
    nvidia-smi
    sudo docker ps -a
    sudo docker volume ls
    sudo docker logs --tail 80 basai-stt-stage66-basai-stt-1
    sudo docker inspect basai-stt-stage66-basai-stt-1 --format '{{json .Mounts}}'
    sudo docker exec bas-ollama ollama list
    curl --max-time 5 -sS -o /dev/null -w '%{http_code}\n' http://127.0.0.1:18066/health/live

## Known incident
STT exited on 9 November 2026 with exit code 255 and restart policy no. Docker restart logs exist on that date. OOMKilled=false. These facts do not conclusively establish the exit root cause. Inspect the host's journal and container runtime state before remediation.

## Controlled deployment
1. Audit current Compose, mounts, image IDs and environment variable *names* (never publish secret values).
2. Back up sanitized Compose and keep private protected .env separately from Git.
3. Ensure the STT model volume remains mapped to the existing Docker volume.
4. Validate candidate Compose without printing secret-expanded configuration.
5. Obtain approval for service recreation, then change only the intended service.
6. Verify health, audio inference, CUDA memory, restart recovery, and Ollama functionality.
7. Document change and rollback in CHANGELOG.md.

Never use docker compose down -v or delete model volumes. Never restart or rename Ollama as a side effect of repairing STT.

## Data handling
Never commit API keys, .env, model weights, recordings, KTP images, transcripts, case data, SQL dumps or container volumes. Keep logs free of personal data and bearer tokens.
