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
