# BAS-AI — Modul Kamera KTP Mandiri (Sandbox)

## Arsitektur

```
/basai/test  (clone, BUKAN halaman tim)
  └── <livewire:basai.ktp-camera />
         ├── resources/views/livewire/basai/ktp-camera.blade.php
         ├── app/Livewire/Basai/KtpCamera.php
         ├── app/Services/Basai/Ktp/PrivateKtpCaptureService.php
         ├── app/Services/Basai/Ktp/GpuKtpOcrClient.php
         └── GPU .81 via 127.0.0.1:18169 (SSH tunnel)
```

**Batas perubahan:** hanya `resources/views/livewire/bas-ai-test-assistant.blade.php` dari clone (satu tag Livewire), plus 6 berkas modul yang terisolasi. Tidak menyentuh `routes/web.php`, `.env`, `app/Livewire/BasAiAssistant.php`, Blade tim, shared layout, service GPU, atau database SIPP. Jika clone mempunyai panel KTP lama `x-data="basKtpCapture()"`, installer menggantinya dengan satu tag nested component. JavaScript panel lama yang tidak digunakan dapat dibersihkan nanti setelah audit; tidak dipanggil oleh panel baru.

## Instalasi di Laravel .95

Dari checkout lokal repository GPU (jangan checkout/switch branch utama STT):

```bash
cd "$HOME/basai-gpu" || exit 1
git fetch origin feature/gpu-ktp-ocr-v1
mkdir -p /tmp/basai-ktp-camera-module
git archive FETCH_HEAD:gpu/ocr/integration/laravel \
  | tar -xf - -C /tmp/basai-ktp-camera-module
sudo python3 /tmp/basai-ktp-camera-module/sandbox-camera/install_sandbox.py \
  --source /tmp/basai-ktp-camera-module/sandbox-camera \
  --root /var/www/html/basai_tes
```

Installer menolak perubahan jika route GET `/basai/test` tidak menuju clone `BasAiTestAssistant` atau anchor `Rekaman Sidang` tidak dikenali. Ia backup dan memeriksa PHP lint + SHA-256 source tim. Pesan `TERPASANG` artinya berkas lokal sudah disalin, **bukan** berarti tunnel/token sudah benar.

**Jangan menjalankan `chown -R` atau mengubah route GET production.**

## Hubungkan .95 ke .81 secara privat

GPU OCR sudah listen di `127.0.0.1:18069` pada host `.81`. Dibutuhkan tunnel lokal **terpisah** pada `.95`:

```
127.0.0.1:18169 (.95) --SSH--> 127.0.0.1:18069 (.81)
```

Gunakan identitas/SSH key yang sudah diizinkan untuk tunnel STT, bukan menyalin password. Untuk diagnosis identitas:

```bash
sudo systemctl cat basai-gpu-tunnel.service | grep -E '^User=|^ExecStart='
```

Contoh manual (perlu disesuaikan dengan identitas yang sudah berfungsi, dan **ditahan di terminal terpisah**):

```bash
ssh -o BatchMode=yes -o ExitOnForwardFailure=yes \
    -o ServerAliveInterval=30 -o ServerAliveCountMax=3 \
    -N -L 127.0.0.1:18169:127.0.0.1:18069 \
    ngadimin@192.168.16.81
```

Pada `.95`, cek tanpa token: `curl -sS -o /dev/null -w '%{http_code}\n' http://127.0.0.1:18169/health/live` (target HTTP 200).

Isi konfigurasi `.env` Laravel yang sudah ada **secara lokal** (jangan commit dan jangan tampilkan token dalam chat):

```dotenv
BASAI_OCR_URL=http://127.0.0.1:18169
BASAI_OCR_TOKEN=<TOKEN_32_BYTE_HEX_DARI_/opt/basai-ocr/.env_DI_.81>
```

Verifikasi token tanpa mencetak isinya:

```bash
cd /var/www/html/basai_tes || exit 1
sudo -u www-data php artisan config:clear
sudo -u www-data php artisan view:clear
sudo -u www-data php -r '
require "vendor/autoload.php";
$app = require "bootstrap/app.php";
$app->make(\Illuminate\Contracts\Console\Kernel::class)->bootstrap();
$url = rtrim((string) config("basai_ocr.url"), "/")."/health/ready";
$response = \Illuminate\Support\Facades\Http::withToken((string) config("basai_ocr.token"))->timeout(10)->get($url);
print("OCR_READY_HTTP=".$response->status().PHP_EOL);
'
```

Target `OCR_READY_HTTP=200`. Jika belum, **jangan** mengklaim OCR terhubung; UI bisa tampil tetapi pembacaan memberi `OCR_UNAVAILABLE`.

## Validasi

```bash
cd /var/www/html/basai_tes
sudo -u www-data php artisan route:list --path=basai/test -vv
sudo -u www-data php artisan view:cache
```

Buka `https://192.168.16.95/basai_tes/basai/test`, login BAS-AI, temukan **Ambil Data KTP Saksi** sebelum **Rekaman Sidang/Upload Audio**, gunakan **Buka Kamera → Ambil Foto → Baca KTP (GPU)** atau **Upload JPG/PNG → Baca KTP (GPU)**. Pastikan 16 kolom tampil termasuk provinsi, kabupaten/kota, kecamatan, kelurahan/desa; missing fields diberi label. `Submit ke SIPP` sengaja disabled. Jangan gunakan KTP asli dalam log GitHub/browser console.

## Rollback

Output installer menunjukkan folder backup, misalnya `.basai-backup/ktp-camera-20261119T090000Z`.

```bash
sudo python3 /tmp/basai-ktp-camera-module/sandbox-camera/install_sandbox.py \
  --root /var/www/html/basai_tes \
  --rollback /var/www/html/basai_tes/.basai-backup/ktp-camera-<NAMA_SESUAI_OUTPUT>
```

Rollback menolak menghapus file yang telah berubah sejak pemasangan. Tidak memengaruhi halaman utama ataupun GPU OCR.

## Pemindahan ke halaman production

Setelah review tim Laravel dan mapping perkara/sidang SIPP disetujui, cukup panggil `<livewire:basai.ktp-camera />` pada Blade tim. Klien GPU, kamera, dan penyimpanan privat tetap sama. Sebelum mengaktifkan Submit ke SIPP, wajib menambahkan pemetaan saksi, otorisasi perkara/sidang, validasi 11 field prioritas, persetujuan operator, serta audit akses data KTP. **Jangan mengaktifkan SIPP write pada sandbox.**
