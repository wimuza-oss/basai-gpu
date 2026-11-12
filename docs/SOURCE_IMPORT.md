# Import source STT dari server GPU

**Tujuan:** mengimpor source **aktual** FastAPI/Faster-Whisper dari server `192.168.16.81` ke `wimuza-oss/basai-gpu` tanpa mengubah container, image, model, atau directory deployment existing.

**Sumber:** `/opt/basai-stt-stage6.6` (nama deployment saat ini). **Tujuan repository:** `stt/` (nama source production). Prosedur ini tidak melakukan perubahan production.

## Jalur disarankan: arsip allowlist lalu review melalui ChatGPT

Di terminal SSH server GPU, sebagai pengguna biasa (`ngadimin`):

```bash
set -euo pipefail
cd /opt/basai-stt-stage6.6

# Hanya file yang sudah diinventarisasi. Tidak memasukkan .env,
# rekaman, model, fixture, cache, atau backup.
tar -czf /home/ngadimin/basai-stt-source.tar.gz \
  Dockerfile compose.yaml requirements.txt \
  app/__init__.py app/main.py \
  app/api/__init__.py app/api/routes.py \
  app/core/__init__.py app/core/config.py app/core/security.py \
  app/services/__init__.py app/services/audio.py app/services/stt.py

tar -tzf /home/ngadimin/basai-stt-source.tar.gz
sha256sum /home/ngadimin/basai-stt-source.tar.gz
```

Periksa source untuk secret hardcoded **secara lokal** sebelum membagikan file, khususnya `app/core/config.py`, `app/core/security.py`, `compose.yaml` dan `app/api/routes.py`. Jangan kirim nilai secret ke percakapan. Jika source berisi kredensial aktif, sanitasi **salinan arsip**, bukan source production, dan lakukan rotasi kredensial bila pernah terekspos.

Transfer arsip dari server GPU ke komputer operator (jika SSH dapat diakses dari komputer operator):

```bash
scp ngadimin@192.168.16.81:/home/ngadimin/basai-stt-source.tar.gz .
```

Unggah arsip yang sudah diperiksa ke percakapan BAS-AI. Isi file selanjutnya dapat direview dan dimasukkan ke branch GitHub dokumentasi, dengan struktur `stt/app/`, `stt/Dockerfile`, `stt/compose.yaml`, dan `stt/requirements.txt`. **Jangan** memindahkan file `.env`.

## Alternatif: commit langsung dari server menggunakan Git

Koneksi GitHub di ChatGPT tidak otomatis memberi kredensial Git ke server Ubuntu. Gunakan SSH key GitHub yang diotorisasi untuk `wimuza-oss` atau login GitHub CLI pada mesin server; jangan menaruh PAT di URL perintah.

Setelah `git clone` berhasil, gunakan branch yang sudah dibuka untuk PR #1:

```bash
git clone --branch docs/gpu-production-baseline-20261112 \
  git@github.com:wimuza-oss/basai-gpu.git \
  /home/ngadimin/basai-gpu

cd /home/ngadimin/basai-gpu
mkdir -p stt
tar -xzf /home/ngadimin/basai-stt-source.tar.gz -C stt

# Lihat isi source; jangan lanjut jika ada credential aktif.
find stt -type f -print | sort
git add stt/Dockerfile stt/compose.yaml stt/requirements.txt stt/app
git diff --cached --stat
git diff --cached --check
git diff --cached -- stt

# Lanjut hanya setelah reviewed:
git commit -m "feat(stt): import verified GPU inference source"
git push origin docs/gpu-production-baseline-20261112
```

Apabila Git SSH belum dikonfigurasi, gunakan jalur arsip di atas; tidak perlu mengubah SSH, Docker, maupun package host hanya untuk unggah source.

## Pemeriksaan keselamatan

- Arsip yang dihasilkan **tidak** mencakup `.env`, token API, data perkara, rekaman, foto KTP, models, log, file fixture, atau file `test*`.
- `.gitignore` adalah pertahanan tambahan, **bukan pengganti review**. Jangan pernah menjalankan `git add -f` untuk secret.
- Jangan menjalankan `docker compose up`, `down`, `down -v`, `systemctl restart docker`, atau mengubah nama deployment saat proses impor source.
- Cek PR #1 sesudah push. Branch `main` baru berubah bila PR secara sadar digabungkan.

## Setelah source ditinjau

1. Audit kontrak API aktual (routes, security, audio dan STT service).
2. Finalkan Compose production dengan external STT volume `basai-stt-stage66_basai_models`.
3. Rencanakan cutover service yang reversible dan validasi inferensi.
4. Dokumentasikan perubahan dan rollback di `CHANGELOG.md`.
