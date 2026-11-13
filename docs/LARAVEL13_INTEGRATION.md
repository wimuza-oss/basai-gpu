# Integrasi BAS-AI ke Laravel 13

Status dokumen: **WAJIB** untuk integrasi BAS-AI Laravel 13.

## Tujuan

Modul BAS-AI harus dapat dipindahkan ke aplikasi Laravel 13 milik tim lain tanpa ketergantungan pada struktur aplikasi sementara, tanpa menyimpan kredensial di repository, dan tanpa mengubah layanan lain di host.

Alur target:

```text
Laravel 13
  -> AudioSource (Laravel filesystem)
  -> FFmpeg normalizer (WAV PCM 16 kHz mono)
  -> GPU Whisper client
  -> transcription result
  -> application service / persistence milik tim Laravel
```

GPU inference tetap merupakan layanan terpisah. Laravel hanya menjadi orkestrator dan client.

## Kontrak konfigurasi WAJIB

### 1. `config/basai.php`

Key berikut wajib tersedia dan harus dibaca melalui `config()`, bukan `env()` dari service/controller:

```php
'pipeline' => [
    'work_directory' => env('BASAI_WORK_DIRECTORY', '/var/lib/basai-tes/work'),
    'max_source_bytes' => (int) env('BASAI_MAX_SOURCE_BYTES', 2147483648),
    'source_disks' => array_values(array_filter(array_map(
        'trim',
        explode(',', env('BASAI_SOURCE_DISKS', 'basai_originals'))
    ))),
],
```

**WAJIB:** `config('basai.pipeline')` menghasilkan array.

**WAJIB:** `config('basai.pipeline.source_disks')` mengandung `basai_originals` pada instalasi sementara di `basai_tes`.

### 2. `config/filesystems.php`

Disk lokal untuk audio sumber wajib didefinisikan:

```php
'basai_originals' => [
    'driver' => 'local',
    'root' => env('BASAI_ORIGINALS_ROOT', '/var/lib/basai-tes/originals'),
    'visibility' => 'private',
    'throw' => true,
],
```

Service tidak boleh mengakses path sumber dengan hard-coded absolute path. Gunakan `Storage::disk(...)`.

### 3. Environment

Nilai deploy-specific wajib berada di environment dan dicontohkan sebagai placeholder di `.env.example`. Jangan commit `.env`, token, password, rekaman, data perkara, model AI, atau hasil transkripsi berisi data perkara.

Contoh non-secret:

```dotenv
BASAI_GPU_BASE_URL=http://127.0.0.1:18167
BASAI_WORK_DIRECTORY=/var/lib/basai-tes/work
BASAI_ORIGINALS_ROOT=/var/lib/basai-tes/originals
BASAI_MAX_SOURCE_BYTES=2147483648
BASAI_SOURCE_DISKS=basai_originals
```

## Bootstrap Laravel: aturan diagnosis

Diagnosis konfigurasi **WAJIB dilakukan setelah Laravel bootstrap**.

Valid:

```bash
php artisan tinker --execute='dump(config("basai.pipeline"));'
```

Tidak valid sebagai diagnosis Laravel:

```bash
php -r 'var_export(require "config/basai.php");'
```

Alasan: file konfigurasi Laravel memang boleh memakai helper `env()`, tetapi helper/config repository harus dinilai dalam lifecycle Laravel. Skrip standalone dapat menghasilkan diagnosis palsu atau perilaku yang berbeda dari Artisan / HTTP runtime.

## Config cache

Jika isi `config/basai.php` benar tetapi `config('basai.pipeline')` tetap `null`, audit `app()->configurationIsCached()`.

Perubahan konfigurasi pada aplikasi sementara hanya boleh dilakukan setelah backup file terkait. Setelah patch terverifikasi secara statis, cache konfigurasi aplikasi **basai_tes saja** dapat dibersihkan:

```bash
php artisan config:clear
```

Kemudian validasi ulang key yang berubah. Jangan menjalankan operasi global Apache, aplikasi Laravel lain, SIPP/BAS, atau Docker GPU untuk memperbaiki cache aplikasi ini.

## LaravelDiskAudioSource

Lokasi saat ini:

```text
app/Services/Basai/Pipeline/LaravelDiskAudioSource.php
```

Kontrak:

- allowlist disk berasal dari `config('basai.pipeline.source_disks', [])`;
- `basai_originals` harus diterima bila ada pada allowlist;
- stream dibuka lewat `Storage::disk($disk)->readStream($path)`;
- path traversal dan disk di luar allowlist harus ditolak;
- error harus eksplisit dan tidak menampilkan kredensial.

Jika `basai.pipeline` tidak termuat, penolakan `basai_originals` adalah efek turunan yang diharapkan dari allowlist kosong. Jangan mengubah keamanan allowlist untuk menutupi masalah konfigurasi.

## FFmpeg WAJIB

Pipeline harus menormalisasi sumber audio sebelum dikirim ke Whisper. Target interoperabilitas:

```text
WAV / PCM signed 16-bit little-endian / 16 kHz / mono
```

Implementasi harus:

- menggunakan executable FFmpeg dari konfigurasi atau PATH;
- memakai process API dengan argument array, bukan shell concatenation;
- mempunyai timeout;
- memeriksa exit code;
- menyimpan temporary file hanya pada work directory BAS-AI;
- cleanup file temporary pada success maupun failure;
- tidak overwrite sumber audio.

## GPU Whisper WAJIB

Kondisi yang sudah lulus dan **tidak perlu diulang tanpa alasan teknis**:

- GPU host: `192.168.16.81`;
- tunnel Laravel host: `127.0.0.1:18167`;
- systemd tunnel aktif;
- `php artisan basai:gpu-status` => CONNECTED;
- CUDA available;
- model loaded.

Client GPU harus memakai endpoint dari konfigurasi, timeout eksplisit, error mapping yang stabil, dan tidak hard-code kredensial.

## Urutan verifikasi integrasi

1. Audit read-only konfigurasi Laravel yang benar-benar ter-bootstrap. **SELESAI**
2. Backup `config/basai.php` sebelum patch. **SELESAI**
3. Perbaiki nesting `basai.gpu.pipeline` menjadi `basai.pipeline`. **SELESAI**
4. Verifikasi `basai.pipeline` dan `basai_originals`. **SELESAI**
5. Verifikasi FFmpeg tersedia. **SELESAI — ffmpeg/ffprobe 4.4.2**
6. Implementasi normalizer FFmpeg. **SELESAI — syntax/config verified; runtime conversion digabung ke E2E**
7. Uji transkripsi WAV melalui client GPU yang sudah terbukti terkoneksi. **PENDING**
8. Dokumentasikan hasil, rollback, dan file yang berubah. **BERJALAN**

## Batas perubahan

Tanpa persetujuan eksplisit, integrasi ini tidak boleh:

- mengubah aplikasi Laravel lain;
- mengubah konfigurasi Apache global;
- mengubah SIPP atau BAS existing;
- mengubah Docker / model / service GPU;
- memindahkan atau menghapus rekaman nyata;
- menampilkan atau commit kredensial.

## Rollback

Setiap patch server harus memiliki backup timestamped sebelum edit. Rollback adalah restore file backup lalu membersihkan cache konfigurasi **hanya aplikasi basai_tes** bila konfigurasi pernah dicache ulang.


## Existing pipeline components

Audit 2026-11-13 menemukan komponen berikut pada Laravel 13 sementara:

```text
app/Services/Basai/
├── GpuSttClient.php
├── RecordingStorageService.php
└── Pipeline/
    ├── AudioSource.php
    ├── AudioStager.php
    └── LaravelDiskAudioSource.php
```

### LaravelDiskAudioSource

Komponen ini menjadi boundary sumber audio. WAJIB dipertahankan:

- disk harus berada pada allowlist `basai.pipeline.source_disks`;
- absolute path ditolak;
- backslash dan NUL ditolak;
- traversal `.` / `..` ditolak;
- stream dibaca melalui Laravel Storage.

### AudioStager

Komponen ini menjadi staging boundary sebelum proses native/remote:

- membuat local temporary copy pada `basai.pipeline.work_directory`;
- membatasi source bytes;
- menghitung SHA-256 selama streaming;
- mendukung expected checksum;
- cleanup stream dan temporary file melalui `finally`.

Jangan mengganti kedua komponen tersebut dengan upload langsung ke GPU.

### Process execution

PHP `proc_open`, Laravel Process facade, dan Symfony Process tersedia. FFmpeg normalizer harus menggunakan process API dengan argument array dan timeout; jangan menggunakan shell command concatenation dari input pengguna.

### Test page integration

Halaman test yang akan dibuat harus mengikuti:

```text
HTTP upload / MediaRecorder
 -> RecordingStorageService
 -> basai_originals
 -> LaravelDiskAudioSource
 -> AudioStager
 -> FFmpeg normalizer
 -> GpuSttClient
 -> response/result
```

Sebelum implementasi controller, baca penuh kontrak `GpuSttClient` dan `RecordingStorageService` yang existing.


## GPU transcription API contract

Kontrak endpoint yang dipakai integrasi Laravel:

```text
POST /v1/stt/transcribe
Content-Type: multipart/form-data
X-BASAI-Key: <secret>
file: audio/wav
```

Laravel memanggil endpoint melalui:

```text
http://127.0.0.1:18167/v1/stt/transcribe
```

Respons sukses memuat:

- `status`
- `language`
- `model`
- `device`
- `processing_seconds`
- `segments[]` dengan informasi segment/timestamp/text/review

Kontrak ini sudah dikenal dari pengujian GPU sebelumnya. Jangan membuat endpoint transkripsi alternatif pada Laravel.

## Remaining verification budget

Untuk mencegah audit berulang, sisa verifikasi dibatasi:

1. FFmpeg tersedia dan normalisasi berhasil.
2. Satu uji end-to-end WAV -> GPU Whisper.
3. Satu uji UI upload/recording.

Setelah tiga gerbang tersebut lulus, hentikan audit berulang dan lanjutkan integrasi aplikasi tim.


## Host dependency: FFmpeg

FFmpeg merupakan dependency **WAJIB** pada host Laravel untuk normalisasi audio menjadi format input Whisper yang konsisten.

Target host:

```text
192.168.16.95
Ubuntu 22.04
```

Paket yang disetujui:

```text
ffmpeg 7:4.4.2-0ubuntu0.22.04.1
```

Kebijakan:

- install melalui repository Ubuntu resmi;
- jangan menggunakan binary acak dari internet;
- aplikasi Laravel menjalankan FFmpeg melalui Laravel Process API / Symfony Process;
- input user tidak boleh digabungkan menjadi shell command string;
- output normalisasi: WAV, PCM signed 16-bit little-endian, 16 kHz, mono;
- source original tidak boleh ditimpa;
- temporary output wajib dibersihkan setelah proses.
