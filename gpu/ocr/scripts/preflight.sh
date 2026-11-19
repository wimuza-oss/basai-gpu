#!/usr/bin/env bash
set -euo pipefail
printf '\n=== BAS-AI OCR GPU PRECHECK (read-only) ===\n'
command -v docker
command -v nvidia-smi
nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader
if ss -H -ltn '( sport = :18069 )' | grep -q .; then
  echo 'STOP: port 18069 sudah dipakai'; exit 1
fi
printf 'Port 18069 bebas\n'
docker compose version
docker info --format 'Runtimes={{json .Runtimes}}' | cut -c 1-300
printf '\nContainer GPU lain (jangan diubah):\n'
docker ps --format '{{.Names}}\t{{.Status}}\t{{.Ports}}' | grep -E 'basai|ollama' || true
