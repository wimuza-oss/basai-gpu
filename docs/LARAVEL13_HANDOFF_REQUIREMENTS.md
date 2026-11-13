# BAS-AI — Kontrak Integrasi Laravel 13 (WAJIB untuk handoff)

**Tanggal baseline:** 2026-11-13  
**Pemilik UI, autentikasi, dan skema aplikasi final:** tim Laravel  
**Pemilik kontrak GPU dan integrasi:** tim integrasi BAS-AI  
**Status dokumen:** persyaratan handoff, bukan berita acara bahwa semua item sudah selesai.

## Prinsip yang tidak boleh dilanggar

- **WAJIB** memenuhi *perilaku/kontrak* di bawah; **TIDAK WAJIB** menyalin class, nama table, mekanisme upload, maupun direktori storage milik `basai_tes`.
- Aplikasi final harus **memiliki satu implementasi storage, satu alur rekaman, satu autentikasi, satu skema metadata, dan satu queue** yang disepakati. Hindari duplikasi modul `basai_tes` jika tim final sudah mengimplementasikannya dengan benar.
- File asli rekaman adalah sumber bukti/rujukan. Simpan privat dan jangan timpa saat konversi; **GPU bukan sistem penyimpanan permanen**.
- Endpoint FastAPI STT saat ini adalah sinkron, bukan streaming/live websocket. *Live recording* di browser berarti capture dan upload potongan ke Laravel; live transcription perlu pipeline inkremental tambahan.
- Perubahan aplikasi lain di server 192.168.16.95, SIPP, BAS existing, atau GPU production dilarang tanpa review/persetujuan.

## Matriks wajib: status per 2026-11-13

| ID | Kewajiban aplikasi Laravel final | Implementasi tim final boleh berbeda? | Status terverifikasi |
| --- | --- | --- | --- |
| M01 | PP login, otorisasi akses perkara/rekaman dan izin tindakan berbasis kepemilikan perkara | Ya, pakai auth tim final | Belum terintegrasi |
| M02 | Upload dan/atau rekam: audio asli disimpan **privat** dan hanya dapat diakses sesuai otorisasi | Ya | Storage service `basai_tes` hanya lulus sintaks; belum lulus uji fungsional |
| M03 | Capture browser bertahap: urutan chunk, deduplikasi, resume, finalisasi, deteksi chunk hilang bila fitur *rekam* berbasis browser dipakai | Ya | Belum dibuat |
| M04 | Validasi file asli dan format hasil (bukan ekstensi saja), durasi, ukuran, jumlah kanal, integritas checksum; batas upload dan kuota storage | Ya | Belum lengkap |
| M05 | Normalisasi/segmentasi dengan FFmpeg untuk PCM WAV, durasi <=600 s dan ukuran <=256 MiB per request; kanal asli dipertahankan jika diperlukan | Ya | Belum dibuat |
| M06 | **Durable queue** dari rekaman/finalisasi ke STT; concurrency 1 untuk layanan GPU ini, retry/backoff untuk 429/503/koneksi, idempotensi, recovery status | Ya | Belum dibuat |
| M07 | HTTP client ke FastAPI GPU melalui alamat privat; autentikasi `X-BASAI-Key`; batas waktu; error sanitization; *no key in logs* | Ya, atau adopsi `GpuSttClient` | Readiness Laravel CLI **lulus**; transkripsi dari Laravel belum diuji |
| M08 | Config yang dapat dipindahkan ke deployment final: GPU URL, API key, timeout, storage, queue, worker; secret di env/secret store, bukan Git | Ya, kunci config boleh berbeda asal dipetakan | GPU URL/key readiness terbukti pada `basai_tes` |
| M09 | Metadata durable: recording ID, perkara ID, pengguna PP, timestamps, source format, hash, status job, chunk/segment index, processing result, error code, retry count | Ya, skema milik tim final | Belum ditetapkan |
| M10 | Penyimpanan respons segmen transkripsi dengan timestamp/channel hint; seluruh transkrip status **NEEDS_REVIEW** sebelum dipakai BAS | Ya | GPU mengembalikan NEEDS_REVIEW; review UI belum dibuat |
| M11 | Proteksi keamanan: CSRF/session, policy per-perkara, batas upload, validasi media, audit log akses, HTTPS untuk UI, penyimpanan tanpa URL publik, retention dan backup | Ya | Belum diaudit |
| M12 | Observability: job IDs, waktu pemrosesan, error dan retry metrics, health monitoring GPU dan tunnel; tidak mencatat audio/key/transkrip sensitif | Ya | Readiness dan systemd tunnel aktif; monitoring end-to-end belum |
| M13 | Prosedur instalasi Laravel final dengan migrasi yang direview dan rollback; tidak menimpa APP_KEY, auth, routes, storage, database tim final | Ya | Pending handoff |
| M14 | Uji penerimaan: upload, capture, >10 menit, gagal jaringan GPU, 429, 401, recovery worker, batas akses PP, penyusunan draft BAS dengan review | Tidak, kriteria tetap | Belum dilakukan |

## Kontrak GPU yang ada (implementasi saat ini)

- Host GPU: `192.168.16.81`, STT bound `127.0.0.1:18066` (jangan expose publik).
- Host Laravel sementara: `192.168.16.95`, **service systemd** `basai-gpu-tunnel.service`, URL lokal `http://127.0.0.1:18167`.
- `GET /health/live` (tanpa auth): `{"status":"alive"}`.
- `GET /health/ready` dengan `X-BASAI-Key`: `status=cuda_available`, `model_loaded` bisa berupa string `"true"`/`"false"`.
- `POST /v1/stt/transcribe` dengan `X-BASAI-Key` dan multipart field `file` (PCM WAV).
- Default batas: 600 detik, 256 MiB, 1–8 channel, sample rate 8k–192k Hz, sample width 2/3/4 byte, satu inferensi per proses GPU; 429 jika sibuk. GPU dapat memerlukan waktu pemrosesan bervariasi, bukan SLA <30 detik.
- Output: `status=NEEDS_REVIEW`, `segments`, model/device, durasi pemrosesan, sha256. Segment menyertakan `channel_no`, `speaker_role_hint`, waktu, `raw_text`. Speaker hint **bukan verifikasi identitas**.
- Error: 401 unauthorized, 413 too large, 415 not WAV, 422 invalid content, 429 GPU busy, 503 unavailable/failed.
- **Tidak ada endpoint GPU untuk live streaming, OCR, LLM, atau async job di API STT ini.** Jangan menamai fitur yang belum ada sebagai sudah siap.

## Komponen yang BOLEH DIPAKAI DARI APLIKASI TIM

- Frontend Upload/Rekam/Pause/Resume/Stop, termasuk teknik chunk dan penyimpanan lokal browser.
- Disk/storage backend (filesystem/NAS/object storage) selama privat, durable, terotorisasi.
- Model DB dan migrasi final, selama metadata wajib tersedia.
- Login SIPP/PP, role/permission middleware, case filter dan dashboard.
- Queue backend Redis/database/Horizon/supervisor atau systemd, selama durable, terbatas concurrency, dan retry benar.
- Validasi file/durasi dan FFmpeg pipeline milik tim, jika memenuhi kontrak GPU.

## Bagian yang bisa DIADOPSI/DITULIS ULANG

- `config/basai.php` (atau konfigurasi ekuivalen tim).
- `App\Services\Basai\GpuSttClient`, exception, dan artisan status command (opsional menyalin persis; wajib perilakunya).
- Systemd tunnel di level server .95 adalah shared infra, tidak perlu digandakan per Laravel app; pastikan ownership, key, firewall dan port loopback dikelola secara eksplisit.
- Perintah `basai:gpu-status` bukan bukti transkripsi berhasil; perlu pengujian end-to-end terpisah.

## Pemeriksaan konfigurasi pipeline dan uji WAV

Audit read-only dari sesi SSH operator pada 13 November 2026 memuat console kernel Laravel. Konfigurasi efektif dan proses pembanding menghasilkan hasil yang sama.

```text
cache=no pipeline=null allowlist=null disk_registered=yes disk_allowed=no
```

Disk `basai_originals` sudah terdaftar. Laravel tidak memuat nilai efektif untuk `basai.pipeline` serta `basai.pipeline.source_disks`. Cache konfigurasi nonaktif pada kedua proses. Skrip lama yang memuat `config/basai.php` langsung dari PHP tanpa bootstrap tidak dapat dijadikan acuan untuk konfigurasi runtime. Hasil bootstrap ini mengisolasi masalah ke sumber atau pemetaan konfigurasi pipeline.

**Perbaikan yang disiapkan.** Periksa file konfigurasi dan kunci yang dibaca `LaravelDiskAudioSource` serta `AudioStager`. Setelah membuat backup privat, tambahkan atau perbaiki bagian `pipeline` pada konfigurasi BAS-AI yang sudah ada. Cocokkan `source_disks`, `work_directory` dan `max_source_bytes` dengan implementasi yang terpasang. Gunakan allowlist eksplisit yang memuat `basai_originals` untuk pilot. Pertahankan konfigurasi klien GPU yang sudah lulus readiness. Instalasi patch, verifikasi FFmpeg dan uji WAV melalui Laravel masih tertunda.

**Rollback.** Pulihkan file konfigurasi dari backup dengan mode dan pemilik awal. Cache awal pada audit ini nonaktif. Lakukan verifikasi kunci pipeline melalui bootstrap Artisan setelah pemulihan.

| Area | Persyaratan **WAJIB** | Bukti penerimaan |
| --- | --- | --- |
| Konfigurasi runtime (M08) | Jalankan diagnosis melalui Artisan atau bootstrap console kernel. Untuk adapter yang ada, gunakan array `basai.pipeline` dan allowlist `basai.pipeline.source_disks`. Letakkan pengaturan GPU yang bekerja dan pipeline pada kunci masing-masing. | Nilai efektif bertipe array dan memuat disk sumber yang dimaksud. Hasil tetap benar pada keadaan cache yang dipakai deployment. |
| Disk sumber dan staging (M02, M04) | Disk sumber harus terdaftar di `filesystems.disks`, ada di allowlist eksplisit dan bersifat privat. Adapter menerima disk dan path relatif dari rekaman terotorisasi, memvalidasi path, menyalin dengan stream ke staging privat, menegakkan batas sumber saat streaming, menghitung SHA-256 dan membersihkan file sementara setelah sukses maupun error. | Fixture dapat dibaca oleh identitas worker, checksum cocok, percobaan disk di luar allowlist ditolak. |
| FFmpeg dan FFprobe (M04, M05) | Biner dapat dijalankan oleh worker. Gunakan argumen proses terpisah, timeout terbatas, input lokal yang sudah divalidasi, serta lokasi output privat. Validasi header WAV, codec PCM, durasi, ukuran dan kanal sebelum upload. | FFprobe melaporkan WAV PCM 16-bit yang kompatibel. Pertahankan kanal yang dibutuhkan. Untuk hasil multikanal, konfirmasikan header dapat dibaca oleh versi Python `wave` yang dipakai GPU. |
| Pembagian audio (M05, M09) | Potong sebelum batas durasi dan byte GPU. Simpan offset tiap potongan serta pemetaan kanal dan gunakan keduanya ketika merakit timestamp. | Fixture panjang melewati alur potong dan gabung dengan urutan benar. Batas aktual deployment menjadi acuan jika lebih ketat dari default. |
| Unggah dan transkripsi (M06, M07, M10, M14) | Laravel mengirim WAV via klien GPU terautentikasi, `POST /v1/stt/transcribe`, multipart `file`. Verifikasi checksum respons, simpan status `NEEDS_REVIEW`, segmen dan metadata tanpa mencetak isi audio, transkrip atau kredensial. | Satu fixture ucapan dummy melewati disk → staging → FFmpeg → GPU. Catat status, jumlah segmen, model/device dan kecocokan checksum. Uji queue dan pemulihan mengikuti M06 dan M14. |
| Backup dan rollback (M13) | Sebelum patch, simpan salinan file yang akan diubah dan catat keadaan cache di lokasi privat. Perubahan dan rollback terbatas pada aplikasi target. | File asli dapat dipulihkan dengan mode dan pemilik yang tepat. Pulihkan keadaan cache aplikasi yang sama, lalu cek ulang kunci konfigurasi dan jalur uji yang terdampak. |

### Probe read-only tanpa keluaran rahasia

Jalankan dari root Laravel. Probe menggunakan console kernel sehingga Laravel memuat konfigurasi efektif sebagaimana Artisan.

```bash
php <<'PHP'
<?php
declare(strict_types=1);

try {
    require getcwd().'/vendor/autoload.php';
    $app = require getcwd().'/bootstrap/app.php';
    $app->make(Illuminate\Contracts\Console\Kernel::class)->bootstrap();

    $disk = 'basai_originals';
    $pipeline = config('basai.pipeline');
    $allowed = config('basai.pipeline.source_disks');
    $registered = config('filesystems.disks', []);

    echo json_encode([
        'cache_active' => $app->configurationIsCached(),
        'pipeline_type' => get_debug_type($pipeline),
        'source_disks_type' => get_debug_type($allowed),
        'disk_registered' => is_array($registered)
            && is_array($registered[$disk] ?? null),
        'disk_allowed' => is_array($allowed) && in_array($disk, $allowed, true),
    ], JSON_THROW_ON_ERROR).PHP_EOL;
} catch (Throwable) {
    fwrite(STDERR, "Bootstrap Laravel gagal. Periksa detail secara lokal.\n");
    exit(1);
}
PHP
```

1. Jika hasil masih `null`, periksa struktur `return` pada `config/basai.php` dan path config yang dibaca adapter. Saat cache aktif, bandingkan dengan hasil bootstrap proses terpisah memakai `APP_CONFIG_CACHE` yang menunjuk ke path privat yang belum ada. Perbandingan ini tidak perlu menghapus cache aktif.
2. Jika kunci file sumber salah atau hilang, perbaiki kunci tersebut setelah backup. Jika konfigurasi tanpa cache benar sementara konfigurasi efektif berbeda, perbarui cache aplikasi ini sesuai prosedur deployment dan identitas eksekusinya. Pertahankan pengaturan GPU dan konfigurasi aplikasi lain.
3. Jalankan satu uji dengan fixture ucapan dummy dari disk yang sekarang diizinkan, konversi FFmpeg dan upload WAV lewat klien Laravel yang sudah ada. Keluaran yang diminta ialah metadata verifikasi dari paket WAV dan respons GPU. Pemeriksaan HTTP 200 dan readiness yang telah lulus cukup dirujuk, kecuali perubahan menyentuh jalur tersebut.

**Bukti sebelumnya dari operator:** HTTP 200, tunnel systemd port loopback `18167` aktif, dan Artisan GPU readiness melaporkan CONNECTED, CUDA tersedia dan model dimuat. Audit konfigurasi efektif sudah tercatat di atas. Penerimaan pipeline masih memerlukan verifikasi pascaperbaikan dan pengujian transkripsi Laravel melalui FFmpeg.

## Definisi selesai dan urutan handoff

1. Tim final memberi nama struktur project, skema metadata rekaman/job, disk storage, kebijakan auth/PP, dan worker yang akan dipakai.
2. Pemetaan **M01–M14** ke file/layanan milik tim dilakukan tanpa membuat implementasi ganda.
3. Integrasi GPU service dan job diuji pada data dummy/non-sensitif dahulu.
4. Lulus uji recovery dan audit akses; baru pilot rekaman persidangan dengan prosedur backup/retensi yang disetujui.
5. Catat persetujuan perubahan production, rollback, dan pemilik operasi.

**Status baseline nyata:** `basai_tes` HTTP 200; file config dan service penyimpanan hanya lulus pemeriksaan syntax; Artisan authenticated GPU readiness = CONNECTED/CUDA available/model loaded; systemd tunnel active + enabled. **Belum** end-to-end transcribe via Laravel, belum durable queue, belum integrasi aplikasi tim final.

