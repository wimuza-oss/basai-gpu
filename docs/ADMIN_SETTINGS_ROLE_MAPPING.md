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


## Existing database target

D5 uses the existing MariaDB schema:

```text
server: 192.168.16.121
database: basai
```

No new database should be created.

Before migrations, perform a read-only schema inventory and avoid collisions with existing BAS-AI tables. The application account should have only the minimum privileges required for `basai`, while SIPP/BAS source schemas remain read-only.


## D5A existing schema inventory

Current MariaDB `basai` inventory through ProxySQL:

```text
alembic_version
basai_captures
basai_hearing_completions
jobs
```

There is no Laravel `migrations` table yet.

Policy:

- preserve all Alembic-era tables;
- do not rename/drop legacy tables during D5;
- inspect existing column/foreign-key contracts before introducing hearing/session tables;
- new Laravel-owned schema should be additive and explicitly documented.


## D5 schema decision after legacy-table inspection

Legacy tables establish `hearing_id` and `case_id` as the existing hearing/case identity contract:

- `basai_captures.hearing_id`
- `basai_captures.case_id`
- `basai_hearing_completions.hearing_id`
- `basai_hearing_completions.case_id`

There are no foreign keys in the current schema.

### Important simplification

Do **not** introduce `basai_hearing_sessions` at D5.

A new session table would duplicate the established hearing identity without adding a proven requirement. Speaker mappings will instead be scoped directly by:

```text
hearing_id + case_id
```

If BAS-AI later needs multiple independent recording sessions inside one SIPP hearing, a dedicated session entity can be introduced then with an explicit migration.

### D5 additive tables

Current D5 target:

```text
basai_settings
basai_roles
basai_channel_profiles
basai_channel_profile_items
basai_speaker_mappings
basai_setting_audits
```

Existing tables remain unchanged:

```text
alembic_version
basai_captures
basai_hearing_completions
jobs
```


## Authorization boundary: Laravel Admin vs Database DDL

Laravel Admin privileges and database schema privileges are different layers.

```text
Laravel Admin
-> application authorization
-> may edit permitted BAS-AI settings
-> uses normal runtime DB connection

Database DDL operator
-> deployment/schema maintenance only
-> CREATE/ALTER/DROP when required
-> never exposed to normal Admin UI
```

The runtime account remains least-privilege.

Authorized modification scope for this project is strictly:

```text
database: basai
```

No other database/schema may be altered.
