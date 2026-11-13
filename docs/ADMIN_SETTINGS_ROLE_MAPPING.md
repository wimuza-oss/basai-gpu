# BAS-AI Admin Settings and Role Mapping Architecture

Status: **D5 design baseline**

## Prinsip utama

Konfigurasi BAS-AI dibagi menjadi dua scope:

1. **Global / Satker Settings** — dikelola Admin.
2. **Per Hearing / Session Mapping** — dikelola saat proses sidang.

Jangan menyimpan `SPEAKER_00 = HAKIM` sebagai setting global karena ID diarization bersifat session-scoped dan dapat berubah pada rekaman berikutnya.

## Menu Admin

```text
Admin
└── Pengaturan BAS-AI
    ├── Identitas Satker
    ├── Audio & Perangkat
    ├── Channel Mapping
    ├── Speaker & Role
    ├── Diarization
    ├── Whisper / STT
    ├── Database & Integrasi
    ├── Tampilan / Logo
    └── Diagnostik
```

## 1. Identitas Satker

Contoh konfigurasi:

- nama satker
- kode satker
- nama aplikasi
- logo
- footer
- timezone
- template BAS

## 2. Audio & Perangkat

- audio interface aktif
- jumlah channel: 4 / 8 / dynamic
- sample rate capture
- nama perangkat
- mapping physical input
- shared-channel flag

## 3. Channel Mapping

Contoh default 4-channel:

```text
CH1 = HAKIM
CH2 = PENGGUGAT
CH3 = TERGUGAT
CH4 = SHARED_WITNESS
```

Contoh 8-channel:

```text
CH1 = HAKIM
CH2 = PANITERA_PENGGANTI
CH3 = PENGGUGAT
CH4 = TERGUGAT
CH5 = SAKSI_1
CH6 = SAKSI_2
CH7 = KUASA
CH8 = CADANGAN
```

Mapping harus configurable dan tidak hard-coded di source.

## 4. Speaker & Role

Role catalog global:

- HAKIM
- PANITERA_PENGGANTI
- PENGGUGAT
- TERGUGAT
- SAKSI_1
- SAKSI_2
- KUASA_PENGGUGAT
- KUASA_TERGUGAT
- UNKNOWN

Admin dapat:

- enable/disable role
- mengatur label tampilan
- menentukan urutan
- menentukan role yang boleh memakai shared channel

Admin **tidak** menentukan SPEAKER_00 secara permanen.

## 5. Per-session Speaker Mapping

Saat sidang berlangsung:

```text
Session A
CH4 / SPEAKER_00 -> SAKSI_1
CH4 / SPEAKER_01 -> SAKSI_2
```

Session B dapat berbeda:

```text
CH4 / SPEAKER_00 -> SAKSI_2
CH4 / SPEAKER_01 -> SAKSI_1
```

Mapping tersimpan dengan `hearing_session_id`.

## 6. Diarization Settings

Admin dapat mengatur:

- enabled
- default expected speakers
- min speakers
- max speakers
- confidence threshold
- mark NEEDS_REVIEW threshold
- shared-channel diarization enabled
- diarization service URL (prefer server-managed, not editable by ordinary UI)
- health status

## 7. Whisper / STT Settings

Admin dapat mengatur parameter aman:

- language default
- model profile
- timeout
- auto-process
- review threshold

Secrets/API keys tidak boleh ditampilkan plaintext.

## 8. Database & Integration

Menu database tidak boleh menyimpan credential plaintext yang dapat dibaca ulang dari UI.

Gunakan:

- encrypted secret storage
- masked password field
- connection test
- least-privilege DB account
- audit log perubahan
- environment/service-level override untuk secret kritis

## 9. Authorization

Gunakan privilege yang sudah ada pada SIPP/BAS sebagai gerbang utama.

Contoh permission:

```text
BASAI_SETTINGS_VIEW
BASAI_SETTINGS_EDIT
BASAI_ROLE_MAPPING
BASAI_DIAGNOSTICS
```

Admin settings dan session role mapping sebaiknya dipisah permission-nya.

## 10. Suggested Data Model

```text
basai_settings
- id
- scope
- key
- value_json
- encrypted
- updated_by
- updated_at

basai_roles
- id
- code
- label
- enabled
- sort_order

basai_channel_profiles
- id
- name
- channel_count

basai_channel_profile_items
- profile_id
- channel_index
- role_hint
- shared_role_group

basai_hearing_sessions
- id
- perkara_id
- started_at
- ended_at
- channel_profile_id

basai_speaker_mappings
- id
- hearing_session_id
- channel_index
- diarization_speaker_id
- role_code
- confidence
- confirmed_by
- confirmed_at
```

## 11. Security Requirements

- perubahan settings dicatat ke audit log;
- secret tidak pernah ditampilkan plaintext;
- role mapping per session dapat direvisi dengan history;
- settings yang memengaruhi koneksi GPU/DB hanya dapat diubah admin;
- default aman bila setting tidak tersedia;
- perubahan config tidak boleh memutus session aktif.

## 12. UI Principle

Global settings:

```text
Admin -> Pengaturan BAS-AI
```

Operational mapping:

```text
Sidang -> Speaker Mapping
```

Dengan pemisahan ini, Admin menentukan kebijakan sistem, sedangkan operator/sidang menentukan siapa SPEAKER_00/SPEAKER_01 pada session tersebut.
