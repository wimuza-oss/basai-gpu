# Phase 1 KTP di BAS-AI Laravel

Repositori GPU STT ini menyimpan dua patch untuk checkout BAS-AI Laravel. Untuk sandbox baru yang sudah punya clone Livewire, jalankan `git apply --check` lalu terapkan `ktp-phase-1.patch`, kemudian `ktp-ocr-tesseract.patch`. Periksa setiap patch terhadap checkout saat akan diterapkan. Sandbox yang sudah memakai kedua patch cukup memverifikasi paket sistem dan menjalankan uji di bawah.

## Prasyarat server

Pada Ubuntu, administrator memasang mesin OCR dan data bahasa Indonesia:

```sh
sudo apt-get install -y --no-install-recommends tesseract-ocr tesseract-ocr-ind
tesseract --version
tesseract --list-langs
```

Daftar bahasa harus memuat `ind`. Proses PHP yang melayani Laravel perlu menemukan `tesseract` melalui `PATH` dan dapat menjalankannya melalui `proc_open`. Jika hasil CLI berbeda dari hasil halaman, periksa kedua hal itu pada proses web. PHP juga memerlukan Fileinfo, GD, dan mbstring. Gunakan batas body web/PHP yang dapat menerima gambar 5 MB setelah enkode Base64, misalnya 8 MB atau lebih. Tidak ada pengaturan `.env` khusus untuk adapter ini.

Disk Laravel `local` harus menunjuk ke penyimpanan privat yang bisa ditulis oleh proses aplikasi. Capture menyimpan gambar asli dan metadata minimal di `ktp-captures/{uuid}/`. Tesseract menerima gambar melalui stdin dan mengembalikan hasil melalui stdout.

## Pemindahan ke produksi

1. Bawa kelima kelas KTP dalam `app/Services/Basai/Test/` dari kedua patch. Jika namespace diganti, sesuaikan import pada komponen dan tes.
2. Pindahkan import dan metode `saveKtpCapture()` dari komponen sandbox ke komponen produksi. Pertahankan validasi sesi BAS-AI dan gunakan konteks perkara dan sidang dari komponen produksi.
3. Pindahkan panel KTP dan fungsi Alpine `basKtpCapture` ke Blade produksi. Letakkan panel di atas Rekaman Sidang pada `/?tahap=1`. Pertahankan layout, rute, dan alur audio produksi. Rute sandbox dan rute GPU hanya diperlukan di sandbox.
4. Terapkan prasyarat server, lalu jalankan tes KTP dan audio. Uji sebagai pengguna BAS-AI dengan JPEG atau PNG sintetis sebelum rilis.

## Kriteria uji

Di sandbox, buka `/basai/test?tahap=1`. Unggah gambar sintetis berlabel KTP dan tekan **Simpan/Baca KTP**. Status hasil yang dikenali adalah `OCR_REVIEW`. Kolom hasil harus bisa diedit dan **RAW OCR text** dapat dibuka. Jika muncul `OCR_UNAVAILABLE`, periksa executable dan `proc_open`. Jika muncul `OCR_FAILED`, periksa data bahasa `ind` dan kemampuan proses PHP menjalankan Tesseract. Status `OCR_NO_FIELDS` berarti OCR berjalan dan parser belum menemukan label yang dikenali.

**Submit ke SIPP** tetap nonaktif. Integrasi SIPP menunggu pemetaan skema yang tervalidasi dan harus memakai `perkara_id` serta pihak yang menghadirkan saksi.
