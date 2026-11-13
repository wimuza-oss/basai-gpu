# basai-gpu

BAS-AI GPU inference services dan kontrak integrasi Laravel 13.

## Status

Integrasi sementara sedang diaudit pada aplikasi Laravel 13:

```text
/var/www/html/basai_tes
```

Baseline GPU yang telah lulus tidak perlu diuji ulang tanpa alasan teknis:

- GPU inference: `192.168.16.81`
- local tunnel endpoint: `127.0.0.1:18167`
- Laravel command `basai:gpu-status`: CONNECTED
- CUDA: available
- model: loaded

Isu aktif: `config("basai.pipeline") === null`, sehingga allowlist `LaravelDiskAudioSource` tidak memuat `basai_originals`.

## Dokumen

- `docs/LARAVEL13_INTEGRATION.md` — kontrak portabel dan persyaratan WAJIB.
- `scripts/laravel13/read_only_audit.sh` — audit runtime tanpa mengubah aplikasi.
- `CHANGELOG.md` — riwayat perubahan.

## Security

Jangan commit `.env`, password, token, model AI, rekaman persidangan, dokumen identitas, data perkara, atau hasil transkripsi yang mengandung data perkara.
