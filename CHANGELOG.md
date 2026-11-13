# Changelog

Semua perubahan penting proyek BAS-AI GPU dan integrasi Laravel dicatat di file ini.

## [Unreleased]

### Added
- Dokumen kontrak integrasi Laravel 13 dan persyaratan WAJIB pipeline audio.
- Skrip audit read-only untuk `/var/www/html/basai_tes`.
- Aturan diagnosis konfigurasi melalui bootstrap Laravel untuk mencegah false diagnosis dari skrip standalone.
- Runbook operasional restart/reconnect untuk Laravel dan SSH tunnel GPU.
- Izin penggunaan halaman uji upload/recording khusus `basai_tes` untuk menguji pipeline end-to-end.

### Fixed / Verified
- HTTP `/basai_tes` pulih menjadi 200.
- `.env` dipastikan dapat dibaca dan `APP_KEY` lama dipertahankan.
- Permission `.env` disetel terbatas untuk owner dan group web.
- `basai-gpu-tunnel.service` terverifikasi `enabled`, `active`, `Restart=always`, dan restart delay 10 detik.
- Listener `127.0.0.1:18167` terverifikasi LISTEN oleh proses SSH.
- Tunnel berjalan stabil dengan `Result=success`, `SubState=running`, dan tanpa reconnect loop pada journal saat pemeriksaan.

### Root cause identified
- `config/basai.php` menempatkan `pipeline` di bawah `gpu`, sehingga Laravel membentuk `basai.gpu.pipeline` sementara service membaca `basai.pipeline.*`.
- Perbaikan yang disetujui: pindahkan hanya blok `pipeline` ke level top-level `basai`; jangan mengubah konfigurasi GPU yang telah lulus.

### Fixed / Verified
- `config/basai.php` diperbaiki dari `basai.gpu.pipeline` menjadi top-level `basai.pipeline`.
- `config('basai.pipeline')` terverifikasi sebagai array.
- `config('basai.pipeline.source_disks')` terverifikasi berisi `basai_originals`.
- `LaravelDiskAudioSource` kini menerima disk `basai_originals` melalui allowlist konfigurasi.
- HTTP `/basai_tes` tetap 200 setelah patch konfigurasi.

### Current known issues
- FFmpeg belum ditemukan di PATH pada audit terakhir.

### Verified baseline
- Laravel 13.42.0.
- PHP 8.3.36.
- GPU host `192.168.16.81`.
- `basai:gpu-status` sebelumnya telah lulus: CONNECTED, CUDA available, model loaded.


### Pipeline architecture audit
- `LaravelDiskAudioSource` memvalidasi disk melalui allowlist `basai.pipeline.source_disks` dan menolak absolute path, backslash, NUL, serta traversal `.` / `..`.
- `AudioStager` membuat temporary local copy pada work directory, membatasi ukuran sumber, menghitung SHA-256, memverifikasi optional expected checksum, dan selalu cleanup melalui `finally`.
- Laravel Process facade dan Symfony Process tersedia; implementasi FFmpeg dapat memakai process API tanpa shell concatenation.
- Belum ditemukan route/controller BAS-AI pada audit terakhir.
- Belum ditemukan class normalizer FFmpeg pada audit terakhir.
- Kontrak metode transkripsi pada `GpuSttClient` masih perlu dibaca sebelum membuat test UI agar tidak membuat jalur integrasi paralel.


### GPU transcription contract recovered
- Endpoint transkripsi GPU yang pernah diuji sebelumnya: `POST /v1/stt/transcribe`.
- Request: multipart/form-data field `file`, tipe audio WAV.
- Authentication: header `X-BASAI-Key`.
- Laravel mengakses endpoint tersebut melalui tunnel lokal `127.0.0.1:18167`.
- Respons sukses memuat metadata status/language/model/device/processing_seconds dan `segments[]`.
- Dengan kontrak ini, tidak diperlukan audit tambahan untuk mencari endpoint GPU.
- Sisa verifikasi dibatasi menjadi tiga gerbang: FFmpeg, satu E2E WAV->GPU, satu UI upload/recording.


### Approved host dependency
- 2026-11-13: pemasangan paket OS `ffmpeg` pada host Laravel `192.168.16.95` disetujui karena merupakan dependency wajib untuk normalisasi audio sebelum transkripsi GPU.
- Paket target dari Ubuntu 22.04 repositories: `7:4.4.2-0ubuntu0.22.04.1`.
- Setelah instalasi, verifikasi dibatasi pada satu pengecekan executable/version lalu implementasi `FfmpegAudioNormalizer`.


### FFmpeg verified
- Host Laravel `192.168.16.95` memiliki `/usr/bin/ffmpeg` dan `/usr/bin/ffprobe`.
- Versi terverifikasi: `4.4.2-0ubuntu0.22.04.1`.
- Gerbang verifikasi FFmpeg dinyatakan selesai; tidak perlu diuji ulang tanpa perubahan dependency.


### FFmpeg normalizer implemented
- `FfmpegAudioNormalizer` telah ditambahkan pada Laravel `basai_tes`.
- Syntax PHP lulus.
- Konfigurasi runtime terverifikasi:
  - ffmpeg: `/usr/bin/ffmpeg`
  - ffprobe: `/usr/bin/ffprobe`
  - timeout: `180`
- Normalizer menggunakan Symfony Process dengan argument array, bukan shell command concatenation.
- Output contract: WAV / pcm_s16le / 16 kHz / mono, diverifikasi kembali melalui FFprobe.
- Temporary output dibersihkan melalui `finally`.


### Recording config nesting issue identified
- `RecordingStorageService` membaca `config('basai.recordings.originals_root')`.
- `config/basai.php` masih menempatkan `recordings` di bawah `gpu`, sehingga key runtime yang tersedia adalah `basai.gpu.recordings`.
- Sebelum UI test dibuat, blok `recordings` harus dipindahkan ke top-level `basai.recordings`, sama seperti perbaikan `pipeline`.
- Patch ini akan digabung dengan implementasi halaman test agar tidak menambah siklus audit terpisah.


### Laravel CLI compatibility note
- Laravel 13.42.0 pada host sementara tidak mendukung opsi `php artisan route:list --columns=...`.
- Gunakan `php artisan route:list --path=basai/test` tanpa `--columns`.
- Syntax modul test dan konfigurasi `basai.recordings` / `basai.pipeline` sudah lulus; kegagalan opsi CLI ini bukan kegagalan aplikasi.


### First E2E upload test
- Upload WAV melalui halaman `/basai/test` berhasil mencapai controller, tetapi pipeline mengembalikan pesan generik `Transkripsi gagal. Periksa log BAS-AI.`.
- Root cause belum ditetapkan; next action adalah membaca exception terbaru pada `storage/logs/laravel.log` tanpa mengulang test.
- Jangan mengulang GPU readiness, tunnel, FFmpeg install, atau konfigurasi pipeline yang sudah lulus.


### Audio input format policy
- Input pengguna tidak harus WAV.
- Format input target: WAV, MP3, dan WebM.
- Semua input dinormalisasi secara internal oleh FFmpeg menjadi WAV / PCM signed 16-bit little-endian / 16 kHz / mono sebelum dikirim ke Whisper.
- Konversi MP3 ke WAV tidak meningkatkan kualitas sumber yang sudah lossy; WAV hanya menjadi format internal standar untuk inference.
- Kegagalan E2E pertama bukan disebabkan format WAV. Request telah melewati storage, staging, FFmpeg, dan mencapai GPU; parser Laravel menolak struktur salah satu item `segments` dari respons GPU.


### Fixed GPU segment contract
- Root cause E2E failure: Laravel `GpuSttClient` expected `segments[].text`, while the GPU transcription service returns segment text in `segments[].raw_text`.
- Parser must accept `raw_text` as the primary field and `text` as a compatibility fallback.
- No changes required to tunnel, FFmpeg, Apache, or GPU Docker.


### End-to-end transcription verified
- 2026-11-13: uji upload WAV melalui `/basai/test` berhasil penuh.
- Pipeline yang terbukti bekerja:
  `RecordingStorageService -> LaravelDiskAudioSource -> AudioStager -> FfmpegAudioNormalizer -> GpuSttClient -> Whisper GPU -> Laravel UI`.
- Input test: WAV.
- Original bytes: 324942.
- Normalized bytes: 216654.
- Normalized format: `pcm_s16le`, 16000 Hz, mono.
- GPU model: `turbo`.
- GPU device: `cuda`.
- Language: `id`.
- Processing time: 0.266 seconds.
- Segments: 2.
- GPU status: `NEEDS_REVIEW`.
- Transcript returned successfully to the Laravel page.
- `NEEDS_REVIEW` is treated as a model/result review state, not a transport or pipeline failure.


### Checkpoint: single-stream E2E complete
- Checkpoint 2026-11-13: integrasi Laravel 13 -> FFmpeg -> GPU Whisper -> transcript UI dinyatakan berhasil dan dihentikan sementara pada titik ini.
- Tahap berikutnya yang direncanakan: speaker diarization dan role mapping untuk memisahkan ucapan Hakim, Penggugat, Tergugat, Saksi 1, Saksi 2, dan peran lain.
- Gender suara tidak boleh dijadikan identitas hukum/peran. Role harus dipetakan dari konteks sidang, channel/microphone, atau assignment eksplisit.
- Target output masa depan:
  - Hakim: pertanyaan...
  - Saksi 1: jawaban...
  - Hakim: pertanyaan...
  - Penggugat: jawaban...
