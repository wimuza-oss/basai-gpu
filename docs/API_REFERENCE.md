# GPU STT API Reference

Source: verified Python modules imported from the uploaded server archive on 12 November 2026. Runtime remains offline at last observation; endpoint behavior is **source-reviewed, not live-tested**.

## Endpoints
| Method | Path | Authentication | Behavior |
| --- | --- | --- | --- |
| GET | /health/live | None | Returns `{"status":"alive"}` |
| GET | /health/ready | `X-BASAI-Key` | Checks supported CUDA compute type; reports `status` and string `model_loaded` |
| POST | /v1/stt/transcribe | `X-BASAI-Key` | Multipart upload field `file`, WAV only; synchronous transcription |

## Upload constraints
- Filename must have a `.wav` extension; audio is validated as uncompressed PCM WAV.
- Default maximum payload: 256 MiB.
- Default maximum audio duration: 600 seconds (10 minutes).
- Supported channels: 1-8; sampling rate: 8,000-192,000 Hz; sample width: 2, 3, or 4 bytes.
- The GPU lock allows one inference request at a time per process. Concurrent requests receive HTTP 429 rather than a durable job ID. Laravel must orchestrate queuing.
- Model: `turbo`; device `cuda`; compute type `int8_float16`; language `id`.

## Authentication
Header: `X-BASAI-Key` with the `BASAI_API_KEY` environment variable (minimum 32 characters). The comparison is performed with `hmac.compare_digest`. Do not publish API keys or expose this endpoint publicly. Use an authenticated encrypted/private network between Laravel and GPU.

## Responses
Successful transcription returns `status: NEEDS_REVIEW`, `language`, `model`, `device`, `audio` metadata, an ordered `segments` array, `processing_seconds`, and a SHA-256 hash of the uploaded WAV. Segment fields: `segment_id`, `channel_no`, `speaker_role_hint`, `start_ms`, `end_ms`, `raw_text`, and `needs_review`.

Speaker hints are microphone-channel labels, **not verified speaker identities**. All text needs judicial staff review.

## Error handling
- 401: invalid or absent API key.
- 413: upload exceeds configured limit.
- 415: filename extension not WAV.
- 422: empty/invalid/unsupported audio.
- 429: GPU busy.
- 503: GPU not ready or transcription failed.
- 422 also applies to framework-side request validation (e.g. no file field).

## Production limitations
- Python application title is still `BAS-AI STT Pilot`; remaining pilot terminology must be cleaned in a reviewed code change.
- Only one synchronous STT job per worker process, no durable job queue on GPU.
- Filename extension validation is not a substitute for malware or content checks.
- Upload buffering / temp filesystem 1 GiB, maximum upload 256 MiB; concurrent memory/disk behavior must be measured.
- No OCR endpoint is present in this source.
- No LLM endpoint is present in this source.
- No production load, reliability, accuracy, or Laravel connectivity test has been performed by this import.
