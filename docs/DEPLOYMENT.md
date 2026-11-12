# Deployment STT production

Status: configuration prepared on GitHub; **not deployed to the GPU host**.

Server: `192.168.16.81`; production source path: `/opt/basai-stt`; container: `basai-stt`.
The Compose file references local image `basai-stt:6.6.0`, without rebuilding or pulling it, and external volume `basai-stt-stage66_basai_models` to prevent accidental loss or re-download of the existing model.

## 1. Preflight — read only

Run on the GPU host:

```bash
sudo docker image inspect basai-stt:6.6.0 --format '{{.Id}}'
sudo docker volume inspect basai-stt-stage66_basai_models --format '{{.Mountpoint}}'
sudo docker ps -a --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
sudo docker inspect basai-stt-stage66-basai-stt-1 --format '{{json .Mounts}}'
sudo ss -lntp | grep ':18066' || true
nvidia-smi
```

Do not print `.env` or the output of `docker compose config` (which may expose the API key). Ensure the legacy container is not listening on port 18066 before new service startup.

## 2. Prepare a separate directory without altering legacy deployment

After approval for host file changes, obtain approved source from the reviewed GitHub branch, then place `stt/app`, `stt/requirements.txt`, `stt/Dockerfile`, and `stt/compose.yaml` under `/opt/basai-stt`. Copy the existing `.env` **privately** into the production directory, with permission mode 600; do not create a new API key without coordinating Laravel. Do not commit `.env` to Git or publish it in a shell transcript.

Inspect `/opt/basai-stt/compose.yaml`, compare it against the actual Docker image, and ensure the repo's source version matches the shipped image before upgrading any code. The existing image remains pinned to 6.6.0. Do not run `docker compose build` during this directory-only cutover.

## 3. Validate configuration without leaking secrets

From `/opt/basai-stt`:

```bash
sudo docker compose --env-file .env -f compose.yaml config --quiet
sudo docker image inspect basai-stt:6.6.0 >/dev/null
sudo docker volume inspect basai-stt-stage66_basai_models >/dev/null
```

If you receive an error, stop and diagnose it before making runtime changes. The Compose file uses an explicit existing external volume and the GPU device reservation through `gpus: all`.

## 4. Cutover — requires separate explicit production approval

The production service cannot bind port 18066 while the old service is running with that port. Schedule a maintenance window and record a rollback state. Only then stop the legacy STT service and create the new STT container. **Do not** use `docker compose down -v`, `docker volume rm`, or restart Ollama.

Suggested intended operations (not executed):

```bash
# From the OLD deployment folder:
cd /opt/basai-stt-stage6.6
sudo docker compose stop basai-stt

# From the NEW deployment folder:
cd /opt/basai-stt
sudo docker compose --env-file .env -f compose.yaml up -d --no-build --pull never
```

The source code may still have the internal title `BAS-AI STT Pilot` because image 6.6.0 is not rebuilt by this configuration cutover. Cosmetic label cleanup requires a separately tested image release; do not claim otherwise.

## 5. Acceptance tests

```bash
sudo docker ps --filter name=basai-stt
sudo docker inspect basai-stt --format '{{.State.Status}} {{.State.Health.Status}} {{.HostConfig.RestartPolicy.Name}}'
curl --max-time 5 -fsS http://127.0.0.1:18066/health/live
nvidia-smi
```

Additionally require an authenticated `GET /health/ready` and a successful inference using **authorized non-sensitive** audio. Never paste the API key or transcription of a real case into external logs or GitHub. The liveness check does not prove model loading.

## 6. Rollback if new service fails

After gathering error logs, stop the new STT container from `/opt/basai-stt`. Then return to `/opt/basai-stt-stage6.6` and start its original Compose service. The model volume and image 6.6.0 must remain intact during this process. Verify liveness and inference again. If the legacy source is missing or the original container was destroyed, stop rather than improvising a destructive rebuild.

Do not delete the old source path until both operational acceptance and rollback verification have been recorded.

## Known limits

Current FastAPI source limits WAV duration to 600 seconds and returns 429 if the GPU is busy. The separate Laravel application must queue requests and split long recordings as appropriate. A production-ready case workflow also requires secure internal transport, transcript review and retention policies.
