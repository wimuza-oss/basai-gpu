# Laravel 13 Operations Runbook

Status: **WAJIB dibaca oleh tim Laravel sebelum integrasi BAS-AI dipindahkan dari `basai_tes`.**

## Scope

Host Laravel sementara:

```text
192.168.16.95
/var/www/html/basai_tes
```

GPU inference:

```text
192.168.16.81
```

Endpoint lokal yang digunakan Laravel:

```text
127.0.0.1:18167
```

Dokumen ini tidak menyimpan username sensitif, password, token, private key, atau isi `.env`.

## Laravel startup requirement

`APP_KEY` harus persisten. Jangan menjalankan `php artisan key:generate` pada setiap boot, deploy, reconnect, atau restart.

Kondisi terverifikasi 2026-11-13:

- `.env` tersedia;
- `config('app.key')` terisi;
- HTTP aplikasi kembali 200;
- APP_KEY existing dipertahankan.

Jika HTTP 500 kembali terjadi, cek log aplikasi sebelum regenerasi key.

## SSH tunnel requirement

Tunnel GPU dikelola systemd:

```text
basai-gpu-tunnel.service
```

Kontrak unit:

- `WantedBy=multi-user.target`
- `Wants=network-online.target`
- `After=network-online.target`
- `Restart=always`
- `RestartSec=10`
- `StartLimitIntervalSec=0`
- SSH `BatchMode=yes`
- SSH `ExitOnForwardFailure=yes`
- SSH keepalive aktif
- bind hanya pada `127.0.0.1:18167`

Target perilaku:

```text
host reboot
 -> network-online
 -> systemd starts tunnel
 -> local port 18167 listens
 -> Laravel accesses GPU through localhost

connection lost
 -> SSH keepalive fails
 -> ssh exits
 -> systemd waits 10 seconds
 -> ssh reconnects
 -> local port 18167 listens again
```

## Important verification

`systemctl is-active=active` saja **tidak cukup**.

Keadaan sehat harus memenuhi semuanya:

1. unit `enabled`;
2. unit `active`;
3. local TCP listener `127.0.0.1:18167` tersedia;
4. endpoint GPU dapat diakses melalui listener;
5. tidak ada reconnect loop pada journal.

Pada 2026-11-13 poin 1-2 sudah lulus, tetapi poin 3 belum terbukti karena output pemeriksaan port kosong. Jangan menandai tunnel selesai sebelum poin 3-5 lulus.

## Test UI policy

Halaman testing boleh dibuat pada `basai_tes` untuk:

- upload audio;
- recording melalui browser;
- submit audio ke pipeline;
- menampilkan status normalisasi/transkripsi;
- menampilkan hasil transkripsi dummy/non-sensitive.

WAJIB:

- route khusus test;
- hanya tersedia pada environment non-production atau dibatasi akses;
- memakai application service yang sama dengan integrasi final;
- validasi MIME/ukuran/disk;
- tidak menyimpan data sensitif ke repository;
- tidak bypass `LaravelDiskAudioSource`;
- cleanup temporary files;
- CSRF tetap aktif untuk POST browser;
- recording browser dianggap input tak terpercaya dan tetap divalidasi server-side.

## Pending technical work

1. verifikasi listener tunnel `127.0.0.1:18167`;
2. perbaiki nesting `config/basai.php`;
3. pasang/verifikasi FFmpeg;
4. implementasikan audio normalizer;
5. buat halaman test upload/recording;
6. lakukan WAV -> Whisper end-to-end test.
