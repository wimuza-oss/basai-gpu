# Phase 1 KTP di BAS-AI Laravel

Patch `ktp-phase-1.patch` ditujukan untuk checkout BAS-AI Laravel dengan clone Livewire sandbox yang sudah ada. Terapkan dari root checkout Laravel. Jalankan `git apply --check` sebelum penerapan. Checkout GPU STT hanya menjadi tempat pencatatan patch.

## Sandbox

- `GET /basai/test?tahap=1` memuat clone Livewire dengan middleware autentikasi BAS-AI. Halaman uji GPU STT tersedia di `GET /basai/test/audio` dan POST transkripsi tetap di `/basai/test`.
- Uji kamera dan unggahan menggunakan gambar sintetis JPEG atau PNG. Penyimpanan ada di disk privat `local` melalui `ktp-captures/{uuid}/original.{ext}` dan `capture.json`.
- Hasil yang diharapkan adalah `OCR_UNAVAILABLE` setelah penyimpanan berhasil. Tombol **Submit ke SIPP** tetap nonaktif.

## Pemindahan ke produksi

1. Bawa tiga kelas layanan KTP dari patch beserta dependensinya. Jika namespace `App\\Services\\Basai\\Test` diganti, sesuaikan import pada komponen dan tes.
2. Pindahkan import dan metode `saveKtpCapture()` dari komponen sandbox ke komponen produksi. Pertahankan validasi sesi BAS-AI dan gunakan konteks perkara dan sidang yang sudah tersedia pada komponen produksi.
3. Pindahkan hanya blok panel KTP dan fungsi Alpine `basKtpCapture` dari patch ke Blade produksi. Letakkan panel tepat di atas Rekaman Sidang pada `/?tahap=1`. Pertahankan layout dan alur audio produksi. Perubahan rute sandbox dan rute GPU tidak diperlukan untuk pemindahan ini.
4. Pastikan disk `local` mengarah ke direktori privat dan dapat ditulis oleh proses aplikasi. Pastikan PHP memiliki Fileinfo dan GD serta batas request mengakomodasi enkode Base64 dari gambar 5 MB. Jalankan tes KTP dan audio, lalu verifikasi dengan sesi BAS-AI di browser sebelum rilis.

Patch ini tidak menambah paket, tabel, atau operasi SIPP. OCR dan pemetaan kolom SIPP adalah pekerjaan lanjutan.
