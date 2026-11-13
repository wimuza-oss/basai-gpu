# BAS-AI Diarization Implementation Plan

Status: **Checkpoint implementation baseline**
Tanggal: 2026-11-13

## Keputusan arsitektur

Speaker diarization tidak dimasukkan ke image STT/Whisper yang sudah stabil.

Buat service/container terpisah pada GPU host:

```text
GPU Host
├── basai-stt
│   └── Whisper Turbo / CTranslate2
└── basai-diarization
    └── Speaker diarization engine
```

Alasan:

- meminimalkan risiko regresi pada STT yang sudah E2E PASS;
- dependency diarization berbasis PyTorch berbeda dari CTranslate2 STT;
- model diarization dapat diganti tanpa mengubah API Laravel;
- resource GPU dapat diukur dan dikontrol independen;
- rollback sederhana: stop/remove service diarization tanpa menyentuh STT.

## Engine strategy

### Pilot 4-channel

Jangan diarize seluruh multichannel hasil downmix.

Gunakan:

```text
CH1 Hakim      -> channel identity
CH2 Penggugat  -> channel identity
CH3 Tergugat   -> channel identity
CH4 Shared     -> speaker diarization
                  ├── SPEAKER_00
                  └── SPEAKER_01
```

Diarization hanya diperlukan pada channel yang shared/ambigu.

### 8-channel

Dedicated channel tetap menjadi evidence utama.

Diarization berfungsi sebagai:

- validator;
- fallback;
- shared-channel splitter;
- ambiguity detector.

## Initial engine candidate

Pilot diarization diarahkan ke **pyannote.audio Community-1** pada audio mono 16 kHz per shared channel.

Pertimbangan:

- cocok untuk diarization offline/batch;
- dapat diberi `num_speakers`, `min_speakers`, atau `max_speakers`;
- menyediakan exclusive speaker diarization yang mempermudah alignment dengan timestamp transcript;
- model dapat dijalankan lokal/offline setelah artifacts tersedia.

Engine dibungkus di balik BAS-AI API sehingga Laravel tidak bergantung pada pyannote secara langsung.

## Future engine option

Untuk kebutuhan streaming/live dan model 4/8 speaker, engine dapat dievaluasi ulang ke NVIDIA NeMo tanpa perubahan kontrak Laravel.

## API boundary

Target service contract:

```text
POST /v1/diarize
GET  /health/live
GET  /health/ready
```

Request diarization:

- mono WAV
- PCM s16le
- 16 kHz
- optional expected/min/max speakers

Response canonical:

```json
{
  "status": "ok",
  "segments": [
    {
      "speaker_id": "SPEAKER_00",
      "start_ms": 1200,
      "end_ms": 4700
    }
  ]
}
```

Laravel/session layer melakukan mapping:

```text
(channel_index, speaker_id) -> role
```

Contoh:

```text
(4, SPEAKER_00) -> SAKSI_1
(4, SPEAKER_01) -> SAKSI_2
```

## Resource policy

Sebelum instalasi/model download:

1. audit GPU VRAM saat STT model loaded;
2. audit RAM;
3. audit disk/model cache;
4. audit Docker networks/ports;
5. jangan mengubah container STT existing;
6. pilih port loopback baru yang tidak konflik;
7. model/token tidak boleh masuk Git repository.

## Implementation checkpoints

### D1 — GPU read-only audit
- GPU/VRAM
- running containers
- image/storage
- ports
- Docker network
- STT resource footprint

### D2 — isolated diarization container
- health endpoint
- model load
- no STT regression

### D3 — single shared-channel test
- 2 speakers
- diarization timestamps
- speaker count

### D4 — Whisper + diarization alignment
- canonical speaker turns
- role mapping

### D5 — 4-channel pilot
- CH1/CH2/CH3 channel identity
- CH4 diarization

### D6 — 8-channel expansion
- dynamic channel configuration
- no schema redesign


## D1 result

Status: **PASS**

- GPU: RTX 5060 Ti 16 GB
- VRAM used with basai-stt loaded: ~1.2 GB
- VRAM free: ~14.6 GB
- RAM available: ~26 GB
- /data available: ~1.4 TB
- basai-stt:6.6.0 healthy on 127.0.0.1:18066
- port 18067 reserved for basai-diarization

## D2 dependency baseline

Pinned baseline:

- Python 3.11
- pyannote.audio 4.0.7
- torch 2.10.0
- torchaudio 2.10.0
- torchcodec 0.10.0
- CUDA wheel: cu130

Privacy:

- PYANNOTE_METRICS_ENABLED=0
- HF_HUB_DISABLE_TELEMETRY=1
- Hugging Face token is download-only and must never be committed or baked into the image.
- Runtime model is loaded from a local read-only mount.


## D2A result

Status: **PASS**

```text
MODEL_DOWNLOAD_OK
/data/stt/diarization-models/community-1
size ~33 MiB
```

Model tree includes:

- embedding
- plda
- segmentation

D2B may now build the isolated diarization container using a read-only local model mount. No Hugging Face token is required at runtime.


## D2B result

Status: **PASS**

```text
basai-diarization:1.0.0
127.0.0.1:18067 -> 8000
model: community-1
device: cuda
ready: true
additional VRAM: ~212 MiB
```

Stable STT remained online and unchanged.

Next checkpoint: **D3 single shared-channel diarization test using a real two-speaker WAV**.
