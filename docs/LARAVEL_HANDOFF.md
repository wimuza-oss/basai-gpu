# BAS-AI GPU ↔ Laravel 13: Handoff Contract

Status: handoff specification only. Laravel host 192.168.16.95 already contains another Laravel application. No deployment or Apache changes have been made by this document.

## Ownership
- GPU host: 192.168.16.81, STT container `basai-stt`, internal GPU port `127.0.0.1:18066`.
- Laravel host: 192.168.16.95, planned isolated application `/var/www/html/basai`; do not alter other Laravel sites, virtual hosts, databases, cron or workers.
- This repository is the source of truth for the GPU API; the other team owns their Laravel application.

## What the final Laravel application needs
1. Authentication, authorization, and auditable case/recording ownership.
2. A private storage disk for hearing recordings, OCR images and transcriptions; no `public/storage` exposure for judicial records.
3. A typed STT client in `app/Services/Basai/`, with configuration in `config/basai_stt.php`, reading configuration through `config()`.
4. A durable queue job for transcription, including retry/backoff, job state and idempotency. Do not send recordings to the GPU from a browser.
5. An approved WAV processing pipeline: uncompressed PCM, 8 kHz–192 kHz, 2/3/4-byte sample width, 1–8 channels, <=600 seconds per request, <=256 MiB per request. Split longer audio and restore correct timestamps.
6. Handling of 401, 413, 415, 422, 429, 503 and timeouts without leaking keys, audio or the raw transcript to logs.
7. Human review. All returned transcript segments have `needs_review=true`; `speaker_role_hint` is only a microphone/channel hint, NOT verified identity.
8. Lifecycle policy for temporary audio and transcripts, upload validation, authorization and export back to BAS templates.

## Contract from reviewed Python source
- `GET /health/live` is unauthenticated; returns `{ "status": "alive" }`.
- `GET /health/ready` requires `X-BASAI-Key`; status is `cuda_available` when CUDA compute type is available.
- `POST /v1/stt/transcribe` requires `X-BASAI-Key` and multipart field `file` containing a WAV.
- Success includes `status=NEEDS_REVIEW`, `language`, `model`, `device`, `audio`, `segments`, `processing_seconds`, and `sha256`.
- The GPU service accepts only one concurrent request per worker, and returns HTTP 429 when busy. Laravel must provide queueing.

## Environment variables to copy into the team's existing .env
```dotenv
BASAI_STT_ENABLED=false
BASAI_STT_BASE_URL=http://127.0.0.1:18166
BASAI_STT_API_KEY=
BASAI_STT_CONNECT_TIMEOUT=5
BASAI_STT_TIMEOUT=300
BASAI_STT_MAX_AUDIO_SECONDS=600
```
`BASAI_STT_API_KEY` must be set locally from the GPU secret via an approved secure secret-transfer process. Never commit the real key. Set `BASAI_STT_ENABLED=true` only after the private SSH tunnel or approved TLS transport is working.

## config/basai_stt.php
```php
<?php

declare(strict_types=1);

return [
    'enabled' => (bool) env('BASAI_STT_ENABLED', false),
    'base_url' => rtrim((string) env('BASAI_STT_BASE_URL', 'http://127.0.0.1:18166'), '/'),
    'api_key' => (string) env('BASAI_STT_API_KEY', ''),
    'connect_timeout' => (int) env('BASAI_STT_CONNECT_TIMEOUT', 5),
    'timeout' => (int) env('BASAI_STT_TIMEOUT', 300),
    'max_audio_seconds' => (int) env('BASAI_STT_MAX_AUDIO_SECONDS', 600),
];
```

## Transport
Current GPU binding is `127.0.0.1:18066` on 192.168.16.81; it is NOT accessible from 192.168.16.95 by LAN. Use a persistent **private, authenticated** tunnel (proposed local port `127.0.0.1:18166` on Laravel host) or a vetted mTLS reverse proxy. A tunnel should run as its own non-root Linux account with a dedicated SSH key and systemd service. Do not modify the GPU API port binding to `0.0.0.0`.

## Isolation and deploy safety
- The intended temporary Laravel root `/var/www/html/basai` lies beneath the existing Apache DocumentRoot `/var/www/html`. It must be created mode `0700` until a dedicated safe VirtualHost with DocumentRoot `/var/www/html/basai/public` has been independently reviewed.
- Do not run `php artisan migrate`, `composer update`, `php artisan queue:restart`, or change Apache DocumentRoot for existing sites during the temporary skeleton install.
- The team's Laravel app is not replaced by this skeleton. Transfer only reviewed integration classes/configuration into the team's app; preserve its APP_KEY, database, auth and queues.
- When final Laravel app is ready, use the team's production database, not an invented database or SIPP credentials.

## Verification
- GPU STT container already passed one CUDA inference on the operator host: `model=turbo`, `device=cuda`, 8 segments, 7.263 s processing.
- Transport and Laravel end-to-end integration: **not yet tested**.
- Worker auto-recovery, long recordings and concurrency: **not yet tested**.
