# BAS-AI Architecture Notes for Presentation

Status: **Presentation Baseline**
Tanggal checkpoint: 2026-11-13

Dokumen ini merangkum arsitektur BAS-AI untuk bahan presentasi internal dan koordinasi dengan tim Laravel/GPU.

## 1. Tujuan Sistem

BAS-AI dirancang untuk:

- merekam audio persidangan;
- mempertahankan sumber audio multichannel;
- mentranskripsikan percakapan dengan Whisper GPU;
- memisahkan siapa yang berbicara;
- memetakan speaker ke peran hukum;
- menghasilkan transkrip kronologis dan tampilan Tanya/Jawab;
- tetap dapat berjalan pada konfigurasi 4-channel maupun 8-channel.

## 2. Arsitektur Besar

```text
Audio Interface
      │
      ├── Channel 1
      ├── Channel 2
      ├── Channel 3
      ├── Channel 4
      ├── ... sampai Channel 8
      │
      ▼
Per-channel Capture
      │
      ├── Channel Identity
      ├── Signal Level / Dominance
      ├── VAD
      └── Speaker Diarization
      │
      ▼
FFmpeg Normalization
      │
      ▼
Whisper Turbo GPU
      │
      ▼
Timestamp Alignment
      │
      ▼
Speaker / Role Fusion
      │
      ▼
Canonical Transcript
      │
      ├── Transcript kronologis
      ├── Transcript per pembicara
      └── Tampilan Tanya/Jawab
```

## 3. Prinsip Utama

BAS-AI tidak boleh hanya mengandalkan:

- gender suara;
- nomor channel secara hard-coded;
- diarization tanpa konteks channel;
- pola tanya-jawab bergantian secara kaku.

Pendekatan utama adalah:

```text
Channel Identity
      +
Speaker Diarization
      +
Timestamp
      +
Signal Dominance
      +
Operator Role Mapping
      =
Speaker Role + Confidence
```

## 4. Mode 4-Channel

Baseline yang direkomendasikan:

```text
CH1 = Hakim
CH2 = Penggugat
CH3 = Tergugat
CH4 = Shared Witness
      ├── SPEAKER_00 -> Saksi 1
      └── SPEAKER_01 -> Saksi 2
```

Channel 4 diperlakukan sebagai shared channel.

Speaker diarization wajib untuk membedakan Saksi 1 dan Saksi 2 bila menggunakan mikrofon yang sama.

Mapping speaker diarization ke role berlaku per sidang:

```text
CH4 / SPEAKER_00 = SAKSI_1
CH4 / SPEAKER_01 = SAKSI_2
```

## 5. Mode 8-Channel

Baseline yang direkomendasikan:

```text
CH1 = Hakim
CH2 = Panitera Pengganti
CH3 = Penggugat
CH4 = Tergugat
CH5 = Saksi 1
CH6 = Saksi 2
CH7 = Kuasa / pihak tambahan
CH8 = Cadangan / role tambahan
```

Dengan lebih banyak dedicated channel, channel identity menjadi evidence utama.

Diarization tetap dipakai sebagai:

- validator;
- fallback;
- pendeteksi salah mapping;
- pembantu saat satu channel kembali dipakai bersama.

## 6. Jangan Downmix Terlalu Awal

Multichannel harus dipertahankan selama proses identifikasi speaker.

Jangan:

```text
CH1 + CH2 + CH3 + CH4
        ↓
      MONO
        ↓
 diarization saja
```

Gunakan:

```text
CH1 -> analisis sendiri
CH2 -> analisis sendiri
CH3 -> analisis sendiri
CH4 -> analisis sendiri
              ↓
        diarization bila shared
```

Setelah speaker/role diketahui, barulah seluruh hasil digabung berdasarkan timestamp.

## 7. Crosstalk / Microphone Bleed

Satu suara dapat masuk ke lebih dari satu mikrofon.

Karena itu channel identity tidak boleh hanya berdasarkan ada/tidaknya suara.

Contoh:

```text
Hakim berbicara

CH1 = -16 dB
CH4 = -39 dB
```

Maka CH1 dianggap channel dominan.

Fusion engine mempertimbangkan:

- channel dominance;
- diarization speaker;
- timestamp alignment;
- role mapping;
- confidence score.

Jika ambigu:

```text
status = NEEDS_REVIEW
```

## 8. Canonical Transcript

Data utama bukan Tanya/Jawab, tetapi ordered speaker turns.

Contoh:

```json
{
  "start_ms": 5000,
  "end_ms": 9100,
  "channel": 4,
  "speaker_id": "SPEAKER_00",
  "role": "SAKSI_1",
  "text": "Kenal Yang Mulia, saya kakak kandungnya.",
  "confidence": 0.94,
  "needs_review": false
}
```

## 9. Derived View: Tanya/Jawab

Dari canonical transcript:

```text
[00:01] Hakim:
Saudara saksi, apakah saudara kenal dengan penggugat?

[00:05] Saksi 1:
Kenal Yang Mulia, saya kakak kandungnya.
```

Aplikasi dapat membentuk:

```text
TANYA — Hakim
Saudara saksi, apakah saudara kenal dengan penggugat?

JAWAB — Saksi 1
Kenal Yang Mulia, saya kakak kandungnya.
```

Tetapi Tanya/Jawab hanyalah presentation layer.

## 10. Role yang Harus Didukung

Minimum:

- HAKIM
- PANITERA_PENGGANTI
- PENGGUGAT
- TERGUGAT
- SAKSI_1
- SAKSI_2
- KUASA_PENGGUGAT
- KUASA_TERGUGAT
- UNKNOWN

## 11. Portabilitas 4 ke 8 Channel

Database tidak boleh mempunyai struktur tetap:

```text
channel_1
channel_2
...
channel_8
```

Gunakan record dinamis:

```text
audio_streams
- session_id
- channel_index
- source_device
- role_hint
- shared_role_group

speaker_mappings
- session_id
- channel_index
- diarization_speaker_id
- role
- confirmed_by
- confidence
```

Dengan desain ini:

```text
4 channel -> tidak perlu ubah arsitektur
8 channel -> tidak perlu ubah arsitektur
>8 channel -> tetap bisa diperluas
```

## 12. Pembagian Tanggung Jawab

### GPU Server

```text
Whisper STT
Speaker Diarization
Timestamp Alignment
Optional Fusion Preprocessing
```

### Laravel

```text
Session Management
Role Mapping
Speaker Mapping
Persistence
Review Workflow
Tanya/Jawab Builder
UI
BAS integration
```

## 13. Status Saat Checkpoint

Sudah lulus:

- Laravel 13 -> GPU connectivity;
- SSH tunnel auto-start/reconnect;
- FFmpeg / FFprobe;
- WAV normalization;
- Whisper Turbo CUDA;
- transcript kembali ke Laravel;
- E2E single-stream transcription.

Checkpoint E2E:

```text
Input WAV
Original: 324942 bytes
Normalized: 216654 bytes
Format: pcm_s16le / 16000 Hz / mono
GPU model: turbo
Device: cuda
Language: id
Processing: 0.266 s
Segments: 2
Status: NEEDS_REVIEW
```

## 14. Tahap Berikutnya

```text
1. Speaker Diarization API di GPU
2. Per-channel audio handling
3. Shared witness channel mode
4. Speaker-to-role mapping
5. Channel + diarization fusion
6. Confidence / NEEDS_REVIEW
7. 4-channel pilot
8. 8-channel expansion
9. Q&A builder
10. Integration ke BAS final
```

## 15. Pesan Kunci untuk Presentasi

BAS-AI tidak hanya melakukan Speech-to-Text.

Target akhirnya adalah:

```text
"Siapa berbicara, kapan berbicara, apa yang dikatakan,
dan dalam peran apa di dalam persidangan."
```

Arsitektur hybrid channel identity + speaker diarization membuat sistem tetap bekerja pada perangkat 4-channel saat ini, tetapi siap berkembang ke 8-channel tanpa perubahan arsitektur utama.
