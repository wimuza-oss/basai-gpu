# BAS-AI Hybrid Multichannel + Speaker Diarization

Status: **DESIGN BASELINE** untuk tahap setelah single-stream E2E.

## Tujuan

Menghasilkan transcript berlabel peran sidang secara stabil pada dua kondisi:

1. audio interface 4-channel, termasuk skenario Saksi 1 dan Saksi 2 berbagi satu mikrofon/channel;
2. audio interface 8-channel, dengan lebih banyak role mendapat channel dedicated.

Channel identity adalah evidence utama bila channel dedicated. Speaker diarization menjadi evidence tambahan/fallback, terutama untuk shared channel.

## Prinsip

Jangan downmix semua channel sebelum identifikasi speaker.

Pipeline harus mempertahankan channel asli:

```text
Multichannel capture
 -> per-channel audio extraction
 -> per-channel VAD / level analysis
 -> optional per-channel diarization
 -> Whisper STT + timestamps
 -> speaker/role fusion
 -> canonical transcript
 -> Q&A view
```

## 4-channel baseline

Default mapping yang disarankan:

```text
CH1 = Hakim
CH2 = Penggugat
CH3 = Tergugat
CH4 = Shared Witness
      -> diarization required
      -> SPEAKER_A => Saksi 1
      -> SPEAKER_B => Saksi 2
```

Mapping harus configurable per sidang. Jangan hard-code di source code.

Bila Penggugat/Tergugat/Kuasa memakai pola berbeda, operator dapat mengganti role-map tanpa deploy.

## 8-channel baseline

Contoh mapping:

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

Pada 8-channel, diarization tetap dapat dijalankan sebagai validation/fallback, tetapi channel identity menjadi evidence utama untuk dedicated channels.

## Shared-channel diarization

Untuk channel yang role-nya shared:

```text
CH4
 -> VAD
 -> diarization
 -> SPEAKER_00 / SPEAKER_01
 -> operator role mapping
 -> Saksi 1 / Saksi 2
```

Mapping diarization ID ke role berlaku hanya untuk session/sidang tersebut.

## Fusion rules

Canonical speaker label ditentukan dari beberapa evidence:

1. dedicated channel role;
2. per-channel diarization speaker ID;
3. energy dominance / active-channel evidence;
4. timestamp alignment with Whisper segment/word;
5. operator-confirmed role mapping.

Suggested confidence order:

```text
dedicated channel + clean signal
  > shared channel + confirmed diarization mapping
  > channel dominance + diarization agreement
  > diarization only
  > UNKNOWN
```

## Crosstalk / microphone bleed

Satu suara dapat muncul pada beberapa mikrofon. Karena itu channel identity tidak boleh hanya berdasarkan "audio exists on channel".

BAS-AI perlu menyimpan per-segment:

- active channel;
- signal level / dominance;
- diarization speaker;
- mapped role;
- confidence;
- overlap flag.

Jika beberapa channel aktif karena bleed, pilih role berdasarkan channel dominan dan evidence diarization. Bila confidence rendah, tandai NEEDS_REVIEW.

## Canonical transcript schema

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

Role minimum:

- HAKIM
- PANITERA_PENGGANTI
- PENGGUGAT
- TERGUGAT
- SAKSI_1
- SAKSI_2
- KUASA_PENGGUGAT
- KUASA_TERGUGAT
- UNKNOWN

## Q&A view

Q&A bukan data utama. Data utama adalah ordered speaker turns.

Q&A dibentuk sebagai derived view:

```text
Hakim:
Saudara saksi, apakah saudara kenal dengan penggugat?

Saksi 1:
Kenal Yang Mulia, saya kakak kandungnya.
```

atau:

```text
TANYA — Hakim
...

JAWAB — Saksi 1
...
```

Jangan mengasumsikan pola selalu tanya-jawab bergantian karena peserta sidang dapat menyela atau menjawab lebih dari satu turn.

## Model direction

Speaker diarization dapat menggunakan model lokal GPU. Desain BAS-AI tidak boleh mengikat Laravel pada satu vendor/model; expose service contract:

```text
POST /v1/diarize
POST /v1/transcribe
POST /v1/transcribe-diarized   (future optional orchestration)
```

GPU service mengembalikan diarization IDs dan timestamps. Laravel melakukan role mapping/session persistence.

## 4-channel -> 8-channel portability

Database dan service jangan memiliki kolom tetap `channel_1` sampai `channel_8`.

Gunakan entities:

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

Dengan ini 4, 8, atau lebih banyak channel dapat digunakan tanpa perubahan arsitektur.
