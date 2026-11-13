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

## Definisi selesai dan urutan handoff

1. Tim final memberi nama struktur project, skema metadata rekaman/job, disk storage, kebijakan auth/PP, dan worker yang akan dipakai.
2. Pemetaan **M01–M14** ke file/layanan milik tim dilakukan tanpa membuat implementasi ganda.
3. Integrasi GPU service dan job diuji pada data dummy/non-sensitif dahulu.
4. Lulus uji recovery dan audit akses; baru pilot rekaman persidangan dengan prosedur backup/retensi yang disetujui.
5. Catat persetujuan perubahan production, rollback, dan pemilik operasi.

**Status baseline nyata:** `basai_tes` HTTP 200; file config dan service penyimpanan hanya lulus pemeriksaan syntax; Artisan authenticated GPU readiness = CONNECTED/CUDA available/model loaded; systemd tunnel active + enabled. **Belum** end-to-end transcribe via Laravel, belum durable queue, belum integrasi aplikasi tim final.
