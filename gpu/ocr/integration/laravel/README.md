# Adapter Laravel BAS-AI OCR

Untuk checkout `/var/www/html/basai_tes` yang sudah mempunyai `App\Services\Basai\Test\KtpOcrService` dan `KtpCaptureService`:

1. Copy ketiga file adapter/kontrak: `app/Contracts/Basai/KtpOcrService.php`, `app/Services/Basai/Ktp/GpuKtpOcrClient.php`, dan `app/Services/Basai/Test/GpuKtpOcrService.php` ke path yang sama di Laravel.
2. Copy `config/basai_ocr.php` ke Laravel `config/`.
3. Ubah **hanya clone test** `app/Livewire/BasAiTestAssistant.php`:
   - import `TesseractKtpOcrService` diganti `GpuKtpOcrService`;
   - argument `saveKtpCapture(..., TesseractKtpOcrService $ocr)` diganti `GpuKtpOcrService $ocr`.
4. Tambah `BASAI_OCR_URL=http://127.0.0.1:18169` dan `BASAI_OCR_TOKEN=...` pada `.env` Laravel **secara lokal, jangan commit**.
5. Sambungkan tunnel SSH dari .95 ke .81: `127.0.0.1:18169 -> 192.168.16.81:127.0.0.1:18069` dengan user SSH terpisah; uji lewat `curl /health/ready` melalui tunnel. Jika tidak ada port forward localhost .81, `.95` tidak bisa mengakses layanan (memang disengaja).
6. Jalankan `php -l` file baru dan clone, `php artisan optimize:clear` sebagai `www-data`, dan uji menggunakan gambar **sintetis**. Status `OCR_REVIEW` tetap memerlukan koreksi petugas. SIPP write tetap disabled.

## Pemindahan ke halaman utama produksi

Client produksi `App\Services\Basai\Ktp\GpuKtpOcrClient` tidak bergantung pada route/UI maupun namespace `Test`, dan mengikuti `App\Contracts\Basai\KtpOcrService::read(bytes, mime)`. Wrapper `Test\GpuKtpOcrService` hanya kompatibilitas dengan `Test\KtpCaptureService` lama. Untuk promosi, **extract panel KTP dari Blade clone ke Blade component/Livewire component terpisah**, lalu panggil dari halaman utama dan halaman sandbox, bukan copy-paste seluruh `BasAiTestAssistant`. Pastikan konteks `perkara_id`/`sidang_id` berasal dari record aktif, bukan input bebas klien.

**Penting:** kontrak dan client sudah berada pada namespace stabil `App\Contracts\Basai` dan `App\Services\Basai\Ktp`. Sebelum produksi, pindahkan `Test\KtpCaptureService` dan panel UI menjadi komponen/layanan stabil yang memanggil client tersebut; wrapper Test boleh dipertahankan untuk sandbox. Jangan mengubah file tim tanpa persetujuan.

## Pencegahan kebocoran

- Jangan menampilkan token HTTP, RAW OCR, atau NIK di log `laravel.log`, exception tracker, reverse proxy, maupun repo.
- Tunnel SSH harus terenkripsi dan restart otomatis; unit systemd baru harus disetujui admin.
- Endpoint GPU sengaja hanya listen 127.0.0.1 pada host GPU.
- Foto KTP asli tetap di private storage Laravel dan tidak dikirim ke layanan OCR eksternal.

## Sebelas kolom prioritas identitas saksi

Kontrak respons GPU selalu mengirim \`required_fields\`, \`missing_fields\`, dan \`required_complete\` untuk:

\`nik\`, \`nama\`, \`tempat_lahir\`, \`tanggal_lahir\`, \`alamat\`, \`kelurahan_desa\`, \`kecamatan\`, \`kabupaten_kota\`, \`provinsi\`, \`agama\`, \`pekerjaan\`.

Semua input tetap dapat diedit operator. GPU **tidak mengarang nilai** untuk field yang tidak terbaca; \`missing_fields\` harus ditampilkan di UI (label berbahasa Indonesia), dan tidak boleh disamakan dengan nilai yang berhasil dibaca. Status \`OCR_REVIEW\` masih berarti *sebagian teks terbaca*, bukan sebelas kolom lengkap. Sebelum integrasi pengiriman SIPP, validasi semua kolom prioritas terisi, tanggal valid, NIK tepat 16 digit, dokumen sesuai perkara/sidang, dan operator mengonfirmasi. Tombol Submit SIPP tetap nonaktif pada fase ini.

Jangan menyalin panel Livewire dari sandbox langsung ke halaman tim. Ekstrak menjadi komponen mandiri yang memanfaatkan \`App\Services\Basai\Ktp\GpuKtpOcrClient\`.


## Struktur alamat administratif (2026-11-19)

OCR mengembalikan alamat menjadi bagian terpisah: `alamat`, `rt_rw`, `kelurahan_desa`, `kecamatan`, `kabupaten_kota`, `provinsi`. Nama field `kabupaten_kota` digunakan secara umum (bukan berarti semua wilayah berstatus kabupaten). Misalnya pada KTP sintetis dengan header `PROVINSI DKI JAKARTA` dan `JAKARTA BARAT`, hasilnya adalah `provinsi=DKI JAKARTA` dan `kabupaten_kota=JAKARTA BARAT`. Parser hanya membaca wilayah administratif dari **header sebelum NIK**; kota yang tertulis di dekat tanda tangan atau setelah `Kewarganegaraan` tidak boleh dianggap sebagai daerah domisili.

Sekarang terdapat **11 field prioritas** untuk verifikasi identitas saksi: NIK, Nama, Tempat Lahir, Tanggal Lahir, Alamat, Kelurahan/Desa, Kecamatan, Kabupaten/Kota, Provinsi, Agama, Pekerjaan. RT/RW tetap disediakan sebagai field terpisah. Jika data kosong, UI perlu menampilkan kekurangannya; tidak boleh membuat dugaan kabupaten/kota dari kecamatan atau provinsi.

Di Laravel sandbox, tambahkan `kabupaten_kota` dan `provinsi` ke field pada panel KTP; `GpuKtpOcrClient` menerima kedua kunci JSON tanpa perlu menyalin engine GPU ke Laravel. Lihat `integration/laravel/patches/ktp-address-fields-test-ui.patch`. Ini hanya untuk sandbox `bas-ai-test-assistant.blade.php`, bukan halaman milik tim utama. Submit SIPP tetap nonaktif.
