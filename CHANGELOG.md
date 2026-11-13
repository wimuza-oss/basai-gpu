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
