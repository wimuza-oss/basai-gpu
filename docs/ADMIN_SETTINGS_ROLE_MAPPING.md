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


## Pedoman penamaan schema BAS-AI

Pedoman resmi proyek:

### Tabel

```text
basai_captures               -> basai_media_sidang
basai_hearing_completions    -> basai_sidang_sidang
basai_settings               -> basai_setting
basai_roles                  -> basai_peran
basai_channel_profiles       -> basai_profil_channel
basai_channel_profile_items  -> basai_detail_profil_channel
basai_speaker_mappings       -> basai_pembicara
basai_setting_audits         -> basai_audit_pengaturan
```

### Kolom

```text
case_id                  -> perkara_id
hearing_id               -> sidang_id
hearing_date             -> tanggal_sidang
owner_id                 -> userid

kind                     -> jenis
mime                     -> tipe_mime
interrupted              -> terputus
next_index               -> indeks_berikutnya
total_bytes              -> jumlah_byte

setting_group            -> tetap
setting_key              -> tetap
value_type               -> tipe_nilai
value_json               -> nilai_json
description              -> keterangan

code                     -> kode
label/name               -> nama
enabled                  -> aktif
sort_order               -> urutan

channel_count            -> jumlah_channel
channel_index            -> nomor_channel
channel_label            -> nama_channel
role_id                  -> peran_id
shared_role_group        -> kelompok_peran_bersama
diarization_enabled      -> pemisahan_pembicara_aktif

diarization_speaker_id   -> kode_pembicara
confidence               -> tingkat_keyakinan
mapping_source           -> sumber_pemetaan
confirmed_by             -> dikonfirmasi_oleh
confirmed_at             -> dikonfirmasi_pada

created_at               -> dibuat_pada
updated_at               -> diperbarui_pada
```

### Identitas pengguna

`owner_id` ditetapkan menjadi `userid`.

`userid` mengacu pada userid user yang sedang login di SIPP/BAS. BAS-AI tidak membuat identitas pengguna baru dan tidak membuat foreign key lintas-database ke tabel user SIPP/BAS.

```text
owner_id -> userid
```

### Metadata/framework

`alembic_version` dan `jobs` tidak diubah karena merupakan kontrak tool/framework, bukan tabel domain BAS-AI.

Forward SQL: `database/sql/002_indonesianize_basai_schema.sql`  
Rollback SQL: `database/sql/002_indonesianize_basai_schema.rollback.sql`


## Authentication source: SIPP sys_users

BAS-AI does not maintain a separate user directory.

Authentication for Laravel BAS-AI, including `/basai/test`, uses the existing SIPP/BAS user identity from `sys_users`.

```text
SIPP/BAS sys_users
        |
        v
Laravel BAS-AI login/session
        |
        +-- userid
        +-- user identity/profile
        +-- existing SIPP/BAS administrative status
        |
        v
BAS-AI authorization
```

Principles:

- `userid` in `basai_media_sidang` refers to the authenticated SIPP/BAS user.
- BAS-AI does not duplicate user/password records.
- BAS-AI does not store SIPP passwords.
- Existing SIPP/BAS administrator identity is the source for BAS-AI administrator access.
- Laravel must use session-based authentication and CSRF protection after credential verification.
- Password verification must follow the actual legacy SIPP/BAS hashing contract; do not invent or migrate password hashes during this integration.
- No cross-database foreign key is created from `basai` to SIPP.


## SIPP sys_users contract

Read-only inspection confirmed the SIPP authentication table:

```text
soreang.sys_users
primary key: userid
unique login: username
password column: password varchar(100)
account block flag: block
expiry: user_expired
concurrent-login policy: allow_concurrent_login
```

Important conclusions:

- `userid` is the canonical BAS-AI user identity.
- There is no direct administrator flag in `sys_users`.
- BAS-AI administrator authorization must be derived from the existing SIPP group/rule model (for example `sys_user_group`, `sys_groups`, and related rule tables) or from the exact rule used by the existing BAS application.
- Password verification must replicate the existing BAS/SIPP authentication contract exactly; the hash algorithm must be confirmed from existing application code rather than inferred.


## Authentication deployment conclusion

Inspection of the legacy BAS source and Apache configuration found no evidence of BAS application login/shared session and no Apache authentication layer. Apache is acting as a reverse proxy/access layer only.

Therefore BAS-AI Laravel will:

- provide its own login form and Laravel session;
- verify credentials against read-only SIPP `sys_users`;
- use `userid` as the canonical user identity;
- derive BAS-AI administrator authorization from the existing SIPP group/rule model;
- never create a second BAS-AI password/user directory;
- never write authentication state back to the SIPP database.


## SIPP administrator group finding

Read-only inspection of `soreang.sys_groups` confirms:

- `groupid = 1`: `Super Administrator`, enabled.
- `groupid = 2`: `Administrator`, disabled.

BAS-AI must not infer administrator access merely from a group name. The current candidate for active SIPP administrator equivalence is membership in enabled group `1`, subject to confirmation of the `sys_user_group` membership contract.

The SIPP menu authorization model also includes `sys_menu_rule(menuid, ruleid)`; BAS-AI will not mutate these SIPP tables.


## Final BAS-AI admin predicate

The SIPP membership contract is confirmed:

```text
sys_user_group
PRIMARY KEY (userid, groupid)
userid  -> sys_users.userid
groupid -> sys_groups.groupid
```

BAS-AI administrator authorization:

```text
authenticated sys_users.userid
AND EXISTS sys_user_group(userid = current_user, groupid = 1)
AND sys_groups(groupid = 1).enable = 1
```

Group 1 is the enabled `Super Administrator` group.

BAS-AI reads this authorization from SIPP and does not mutate SIPP membership/group data.


## Final BAS-AI login eligibility

SIPP password inventory confirms all current `sys_users.password` values are 32-character hexadecimal hashes compatible with the legacy MD5 contract.

BAS-AI login eligibility is restricted to these SIPP roles only:

1. `Super Administrator` (`groupid=1`);
2. `Panitera/Wakil Panitera` (`groupid=30`);
3. enabled Panitera Muda / Panmud groups;
4. `Panitera Pengganti` (`groupid=500`).

Do **not** authorize by the entire nested-set subtree under `groupid=30`. That subtree also contains roles such as Jurusita and other operational groups that are explicitly not allowed to use BAS-AI.

Recommended policy is an explicit allowlist. For the current SIPP schema, Panmud eligibility should match enabled groups whose role name/description identifies them as Panmud/Panitera Muda, together with the fixed groups above.

A user with multiple SIPP groups is allowed when at least one active membership matches the allowlist.

### BAS-AI administrative privilege

Super Administrator (`groupid=1`) is BAS-AI Admin.

Panitera-hierarchy users are normal BAS-AI operational users unless a later explicit BAS-AI privilege rule grants administration.


### Explicit exclusion

Jurusita is explicitly excluded from BAS-AI login eligibility, even though the SIPP group hierarchy places Jurusita below the Panitera branch.


## SIPP authentication gateway

The BAS-AI runtime account is intentionally not granted direct `SELECT` access to `soreang.sys_users`, `sys_user_group`, or `sys_groups`.

Authentication crosses the schema boundary through a `SQL SECURITY DEFINER` stored procedure owned by database `basai`:

```text
basai.basai_autentikasi_sipp(username, md5)
```

The procedure returns only:

- `userid`
- `fullname`
- `username`
- `admin_basai`

It does not expose the stored SIPP password hash to Laravel.

Eligible roles remain: Super Administrator, Panitera/Wakil Panitera, enabled Panmud/Panitera Muda, and Panitera Pengganti. Jurusita remains excluded.

Laravel runtime receives only `EXECUTE` on the procedure through the ProxySQL backend identity `basai_app@192.168.16.236`.
