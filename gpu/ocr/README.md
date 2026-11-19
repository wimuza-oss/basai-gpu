# BAS-AI OCR GPU — OpenCV + PaddleOCR (PP-OCRv5 Indonesia)

Service OCR privat berbasis **FastAPI**, **OpenCV**, **PaddleOCR PP-OCRv5**, dan **PaddlePaddle GPU CUDA 12.9**. Dirancang untuk GPU NVIDIA Blackwell (RTX 5060 Ti 16 GB) pada host .81, **tanpa mengubah** service STT/diarization/Ollama.

**Status:** paket siap deploy; model PaddlePaddle GPU belum dapat diuji dari luar jaringan `.81`. Jangan nyatakan production-ready sebelum uji Docker real dan KTP sintetis/izin pakai.

## Layout

```text
app/
  main.py            # FastAPI API/auth/validasi/health
  config.py          # token + batas resource
  engine.py          # backend PaddleOCR, normalisasi kotak/row
  preprocess.py      # koreksi perspektif kondisional, CLAHE, denoise, sharpen
  parser.py          # parser label KTP Indonesia; tidak menebak digit
  service.py         # orchestration, multi-pass, scoring dan quality warnings
  warmup.py          # unduh model dengan gambar sintetis pada tahap instalasi
integration/laravel/ # kontrak + client stabil + adapter sandbox + config
compose.yaml         # GPU, loopback binding, container hardening
Dockerfile           # CUDA 12.9 + Paddle GPU wheel
requirements.txt
scripts/
  preflight.sh       # audit sebelum deployment
  smoke.sh           # health + synthetic request tanpa data nyata
```

## Port dan keamanan

- GPU `.81`: `127.0.0.1:18069` ke container port `8000` — **tidak dipublikasikan pada LAN**.
- Endpoint `POST /v1/ktp/ocr`: multipart key `image` (JPEG/PNG, <=5 MB, <=16 megapiksel), Bearer token, JSON.
- `GET /health/live`: liveness lokal; `GET /health/ready`: membutuhkan token dan model siap.
- Tidak menerima URL eksternal untuk OCR, tidak menyimpan gambar / hasil OCR di GPU, tidak memuat data KTP ke GitHub.
- Single worker + semaphore satu request inference per satu waktu. Laravel menyimpan foto setelah OCR `OCR_REVIEW`, tetap perlu review operator.

## Deploy di host GPU 192.168.16.81 (oleh operator / Codex dengan izin)

Ambil source dari branch PR #3 **tanpa mengganti branch kerja STT** dan tanpa menyentuh service yang ada:

```bash
cd "$HOME/basai-gpu" || exit 1
git fetch origin feature/gpu-ktp-ocr-v1
sudo install -d -o ngadimin -g ngadimin -m 0750 /opt/basai-ocr
# Hanya arsip subfolder OCR yang diekstrak.
git archive FETCH_HEAD:gpu/ocr | tar -xf - -C /opt/basai-ocr
cd /opt/basai-ocr || exit 1
bash scripts/preflight.sh
```

> Jangan jalankan `docker compose down` global, jangan menghapus model STT, dan jangan menimpa `/opt/basai-stt` atau `/opt/basai-diarization`.

Siapkan cache model dan token lokal, lalu build service OCR terpisah:

```bash
cd /opt/basai-ocr || exit 1
install -d -m 0700 models
sudo chown 10001:10001 models
umask 077
printf 'BASAI_OCR_TOKEN=%s\n' "$(openssl rand -hex 32)" > .env
chmod 600 .env

docker compose build
# Model weights diunduh pada tahap instalasi menggunakan gambar sintetis.
docker compose run --rm --no-deps basai-ocr python -m app.warmup
docker compose up -d --wait
```

**Jangan lakukan `git add .env`**, token tidak boleh masuk GitHub. Proses warmup dapat mengunduh model dari internet; KTP pengguna tidak ikut. Setelah warmup, audit lokasi cache `/opt/basai-ocr/models` dan konfigurasi isolasi egress sesuai kebijakan institusi.

Cek readiness via token tanpa mencetak token (hanya dari terminal .81):

```bash
set -a; source /opt/basai-ocr/.env; set +a
curl -fsS -H "Authorization: Bearer $BASAI_OCR_TOKEN" http://127.0.0.1:18069/health/ready
# harap status ready dan device gpu:0
```

**Jangan jalankan `curl` dengan foto KTP asli yang merupakan data perkara saat debug pertama.** Gunakan generator sintetis `scripts/smoke.sh`.

## Kontrak respons

```json
{
  "status": "OCR_REVIEW",
  "fields": {"nama": "SAKSI SINTETIS"},
  "raw_text": "Nama: SAKSI SINTETIS",
  "field_confidences": {"nama": 0.97},
  "review_required": true,
  "conflicting_fields": [],
  "quality": {"width": 1000, "height": 600, "sharpness": 120.2, "brightness": 145.0, "warnings": []},
  "warnings": [],
  "engine": "paddleocr-ppocrv5",
  "device": "gpu:0",
  "elapsed_ms": 650
}
```

Respons berisi PII; jangan logging body. `status=OCR_NO_FIELDS` tetap memberikan RAW OCR text jika ada. `review_required=true` selalu. Backend OCR **tidak menulis ke SIPP**.

## Rollback

```bash
cd /opt/basai-ocr
# Hentikan OCR baru saja, tanpa mengubah service GPU lain:
docker compose stop basai-ocr
# Di Laravel: kembalikan tipe class di clone ke TesseractKtpOcrService
# lalu `sudo -u www-data php artisan optimize:clear`.
```

Jangan menghapus `/opt/basai-ocr/models` untuk rollback; cache model bisa dipakai saat update.

## Keterbatasan

- OpenCV dapat mengurangi noise/kemiringan, **tidak dapat mengembalikan huruf/digit yang tidak terekam oleh kamera**. NIK hasil OCR tetap diverifikasi petugas.
- OCR layout tidak otomatis menentukan saksi/pihak SIPP. Pemetaan DB harus diaudit sebelum write.
- Model yang belum berhasil warmup / tidak menemukan GPU = service tidak READY, **tidak fallback CPU diam-diam**.
- CUDA/PaddlePaddle pada RTX 50-series bisa memiliki isu runtime; jika muncul `CUDA error 719`, stop dan audit versi runtime; jangan terus retry dengan data nyata.
- Kinerja/akurasi dokumen nyata hanya dapat dibuktikan di `.81`, tidak dapat dipastikan dari unit test mock.


## Struktur alamat administratif (2026-11-19)

OCR mengembalikan alamat menjadi bagian terpisah: `alamat`, `rt_rw`, `kelurahan_desa`, `kecamatan`, `kabupaten_kota`, `provinsi`. Nama field `kabupaten_kota` digunakan secara umum (bukan berarti semua wilayah berstatus kabupaten). Misalnya pada KTP sintetis dengan header `PROVINSI DKI JAKARTA` dan `JAKARTA BARAT`, hasilnya adalah `provinsi=DKI JAKARTA` dan `kabupaten_kota=JAKARTA BARAT`. Parser hanya membaca wilayah administratif dari **header sebelum NIK**; kota yang tertulis di dekat tanda tangan atau setelah `Kewarganegaraan` tidak boleh dianggap sebagai daerah domisili.

Sekarang terdapat **11 field prioritas** untuk verifikasi identitas saksi: NIK, Nama, Tempat Lahir, Tanggal Lahir, Alamat, Kelurahan/Desa, Kecamatan, Kabupaten/Kota, Provinsi, Agama, Pekerjaan. RT/RW tetap disediakan sebagai field terpisah. Jika data kosong, UI perlu menampilkan kekurangannya; tidak boleh membuat dugaan kabupaten/kota dari kecamatan atau provinsi.

Di Laravel sandbox, tambahkan `kabupaten_kota` dan `provinsi` ke field pada panel KTP; `GpuKtpOcrClient` menerima kedua kunci JSON tanpa perlu menyalin engine GPU ke Laravel. Lihat `integration/laravel/patches/ktp-address-fields-test-ui.patch`. Ini hanya untuk sandbox `bas-ai-test-assistant.blade.php`, bukan halaman milik tim utama. Submit SIPP tetap nonaktif.
