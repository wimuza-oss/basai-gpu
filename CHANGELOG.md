# Changelog

Semua perubahan penting proyek BAS-AI GPU dan integrasi Laravel dicatat di file ini.

## [Unreleased]

### Added
- Dokumen kontrak integrasi Laravel 13 dan persyaratan WAJIB pipeline audio.
- Skrip audit read-only untuk `/var/www/html/basai_tes`.
- Aturan diagnosis konfigurasi melalui bootstrap Laravel untuk mencegah false diagnosis dari skrip standalone.

### Current known issue
- `config("basai.pipeline")` terakhir terobservasi menghasilkan `null`.
- `LaravelDiskAudioSource` menolak `basai_originals` karena allowlist pipeline tidak termuat.
- Perbaikan server belum dicatat sebagai selesai sampai audit runtime pada host Laravel membuktikan penyebab dan patch terverifikasi.

### Verified baseline
- Laravel `basai_tes` HTTP 200.
- Tunnel GPU lokal `127.0.0.1:18167` aktif.
- `basai:gpu-status` telah lulus: CONNECTED, CUDA available, model loaded.
