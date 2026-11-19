# Adapter Laravel BAS-AI OCR

Untuk checkout `/var/www/html/basai_tes` yang sudah mempunyai `App\Services\Basai\Test\KtpOcrService` dan `KtpCaptureService`:

1. Copy `app/Services/Basai/Test/GpuKtpOcrService.php` ke folder sama di checkout Laravel.
2. Copy `config/basai_ocr.php` ke Laravel `config/`.
3. Ubah **hanya clone test** `app/Livewire/BasAiTestAssistant.php`:
   - import `TesseractKtpOcrService` diganti `GpuKtpOcrService`;
   - argument `saveKtpCapture(..., TesseractKtpOcrService $ocr)` diganti `GpuKtpOcrService $ocr`.
4. Tambah `BASAI_OCR_URL=http://127.0.0.1:18169` dan `BASAI_OCR_TOKEN=...` pada `.env` Laravel **secara lokal, jangan commit**.
5. Sambungkan tunnel SSH dari .95 ke .81: `127.0.0.1:18169 -> 192.168.16.81:127.0.0.1:18069` dengan user SSH terpisah; uji lewat `curl /health/ready` melalui tunnel. Jika tidak ada port forward localhost .81, `.95` tidak bisa mengakses layanan (memang disengaja).
6. Jalankan `php -l` file baru dan clone, `php artisan optimize:clear` sebagai `www-data`, dan uji menggunakan gambar **sintetis**. Status `OCR_REVIEW` tetap memerlukan koreksi petugas. SIPP write tetap disabled.

## Pemindahan ke halaman utama produksi

Adapter tidak bergantung pada ID route/UI; `GpuKtpOcrService` memakai kontrak `KtpOcrService::read(bytes, mime)` yang sama. Untuk promosi, **extract panel KTP dari Blade clone ke Blade component/Livewire component terpisah**, lalu panggil dari halaman utama dan halaman sandbox, bukan copy-paste seluruh `BasAiTestAssistant`. Pastikan konteks `perkara_id`/`sidang_id` berasal dari record aktif, bukan input bebas klien.

**Penting:** implementasi awal memakai namespace `App\Services\Basai\Test` karena kompatibilitas dengan `KtpCaptureService` yang sudah ada. Sebelum production, pindahkan interface, capture service, dan adapter menjadi `App\Services\Basai\Ktp` dan buat wrapper backward-compatible di sandbox; jangan mengubah file tim tanpa persetujuan.

## Pencegahan kebocoran

- Jangan menampilkan token HTTP, RAW OCR, atau NIK di log `laravel.log`, exception tracker, reverse proxy, maupun repo.
- Tunnel SSH harus terenkripsi dan restart otomatis; unit systemd baru harus disetujui admin.
- Endpoint GPU sengaja hanya listen 127.0.0.1 pada host GPU.
- Foto KTP asli tetap di private storage Laravel dan tidak dikirim ke layanan OCR eksternal.
