# basai-gpu

BAS-AI GPU inference services dan kontrak integrasi Laravel 13.

## Status

Integrasi sementara sedang diuji pada aplikasi Laravel 13:

```text
/var/www/html/basai_tes
```

### Terverifikasi 2026-11-13

- **E2E transcription: verified** — upload WAV berhasil sampai transcript tampil di Laravel.

- Laravel 13.42.0 / PHP 8.3.36.
- HTTP `/basai_tes` kembali **200**.
- `.env` tersedia dan `APP_KEY` terbaca oleh bootstrap Laravel.
- `APP_KEY` lama dipertahankan; jangan regenerasi pada restart.
- Disk `basai_originals` terdefinisi dan root menunjuk ke `/var/lib/basai-tes/originals`.
- GPU inference: `192.168.16.81`.
- Laravel command `basai:gpu-status` sebelumnya telah lulus: CONNECTED, CUDA available, model loaded.
- Unit `basai-gpu-tunnel.service` terverifikasi `enabled` dan `active`, `Restart=always`, `RestartSec=10s`.
- Listener lokal `127.0.0.1:18167` terverifikasi LISTEN oleh proses SSH.
- Journal tidak menunjukkan reconnect loop; `Result=success`, `SubState=running`.
- `config('basai.pipeline')` terverifikasi valid pada runtime Laravel.
- `basai_originals` terverifikasi masuk allowlist pipeline.
- HTTP tetap 200 setelah perbaikan nesting konfigurasi.
- FFmpeg dan FFprobe 4.4.2 terverifikasi. Uji WAV end-to-end melewati normalisasi PCM 16-bit, 16 kHz, mono dan menampilkan hasil transkripsi di Laravel.

Status di atas adalah hasil verifikasi 2026-11-13. Jika masalah konfigurasi muncul kembali setelah perubahan aplikasi, mulai dengan audit read-only melalui bootstrap Laravel. Periksa `basai.pipeline`, `basai.gpu.pipeline`, dan status cache konfigurasi sebelum memutuskan perlu patch.

## Dokumen

- `docs/LARAVEL13_INTEGRATION.md` — kontrak portabel dan persyaratan WAJIB.
- `docs/LARAVEL13_OPERATIONS.md` — runbook restart/reconnect dan status operasional.
- `docs/PRESENTATION_ARCHITECTURE_NOTES.md` — ringkasan arsitektur 4/8 channel, diarization, dan role mapping untuk bahan presentasi.
- `docs/DIARIZATION_IMPLEMENTATION_PLAN.md` — checkpoint implementasi speaker diarization di GPU.
- `scripts/laravel13/read_only_audit.sh` — audit runtime tanpa mengubah aplikasi.
- `CHANGELOG.md` — riwayat perubahan.

## Halaman uji

Untuk mempercepat integrasi, halaman **upload audio / recording browser** boleh ditambahkan hanya pada `basai_tes`. Halaman ini harus menggunakan service pipeline yang sama dengan integrasi akhir; tidak boleh membuat jalur transkripsi alternatif yang bypass validasi.

## Security

Jangan commit `.env`, password, token, private key SSH, model AI, rekaman persidangan, dokumen identitas, data perkara, atau hasil transkripsi yang mengandung data perkara.
