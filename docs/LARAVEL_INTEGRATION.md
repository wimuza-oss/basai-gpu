# Integrasi Laravel 13 ke layanan STT GPU

**Status:** desain koneksi dan prosedur audit awal. Transport belum dipasang. Tidak mengubah layanan STT yang telah lulus pengujian.

## Host dan tanggung jawab

| Host | Peran | Kondisi |
| --- | --- | --- |
| 192.168.16.95 | Server deployment Laravel 13 (tim aplikasi) | OS, web runtime, queue dan deployment method belum diaudit |
| 192.168.16.81 | Server GPU / Docker STT | `basai-stt` running/healthy, model Turbo CUDA, inference pilot PASS |

GPU bind saat ini: `127.0.0.1:18066:8000` pada host 192.168.16.81. Ini memang **tidak dapat diakses langsung** dari 192.168.16.95.

## Keputusan untuk pilot: outbound encrypted tunnel

Koneksi diprakarsai dari Laravel host 192.168.16.95 menuju port SSH 22 di GPU 192.168.16.81. Tunnel meneruskan port lokal yang dibatasi ke loopback GPU.

Bila Laravel native di host: rencana endpoint internal `http://127.0.0.1:18081` pada host Laravel, forwarded secara privat ke `127.0.0.1:18066` pada GPU.

- Gunakan akun SSH service khusus dengan restricted port-forwarding ke `127.0.0.1:18066` dan key terpisah dari GitHub Deploy Key.
- Sistem service `systemd` dapat menjaga tunnel tetap aktif dengan restart otomatis.
- Lakukan verifikasi host key, serta batasi firewall SSH hanya dari Laravel host sesuai kebijakan jaringan.
- Authentication API `X-BASAI-Key` tetap wajib. Tunnel adalah *transport*, bukan pengganti autentikasi.
- Jangan membuka 18066 GPU ke `0.0.0.0` atau langsung ke internet.

**Jika Laravel di dalam Docker:** `127.0.0.1` di container bukan loopback host. Harus diputuskan desain sidecar tunnel dalam Docker network privat atau endpoint host yang diberi kontrol akses; jangan menyalin pengaturan localhost native tanpa mengaudit mode deployment.

## Read-only host audit (jalankan di 192.168.16.95)

```bash
echo "=== HOST / OS ==="
hostname
cat /etc/os-release | grep '^PRETTY_NAME='
hostname -I
echo "=== ROUTE TO GPU ==="
ip -4 route get 192.168.16.81
echo "=== RUNTIMES ==="
command -v php || true
command -v composer || true
command -v docker || true
command -v ssh || true
command -v systemctl || true
echo "=== TCP SSH REACHABILITY (not authentication) ==="
if timeout 5 bash -c 'exec 3<>/dev/tcp/192.168.16.81/22'; then
  echo "GPU TCP/22 reachable"
else
  echo "GPU TCP/22 unreachable or filtered"
fi
echo "=== PORT PLAN ==="
ss -lnt | grep ':18081 ' || echo "Host port 18081 not currently listening"
```

Perintah tersebut tidak membuat tunnel, tidak mengubah firewall dan tidak membaca credential. Hasil audit digunakan menentukan desain deployment sesuai host aplikasi.

## Kontrak Laravel -> STT (source-reviewed and GPU pilot-tested)

- `GET /health/live`: liveness tanpa authentication.
- `GET /health/ready`: header `X-BASAI-Key`; status `cuda_available`.
- `POST /v1/stt/transcribe`: authenticated multipart field `file`, PCM WAV; output segments, timestamps, SHA256 and `status=NEEDS_REVIEW`.
- Batas engine saat ini: 256 MiB, maksimal 600 detik per WAV, 1-8 channel.
- `429`: GPU busy. Laravel bertanggung jawab atas antrian/retry dengan backoff, idempotensi job dan tidak mengirim permintaan bersamaan tanpa kontrol.
- `503`: engine unavailable; jangan langsung menyimpulkan job selesai.
- `422`: audio invalid atau melanggar batas; perlu validasi sebelum dikirim.
- Audio lebih dari 600 detik membutuhkan chunking / queue workflow yang dirancang terpisah, mempertahankan offset timestamp dan tanpa kehilangan segmen.
- Persistensi audio, transkrip, relasi perkara, retensi, serta persetujuan PP di Laravel, bukan di GPU.
- Jangan menuliskan API key atau isi perkara dalam log, URL, issue GitHub, atau output debugging.

## Bukti pengujian STT yang sudah diterima dari operator

- Docker production `basai-stt` healthy, image `basai-stt:6.6.0`, restart `unless-stopped`.
- Authenticated readiness: `cuda_available` (`model_loaded=false` sebelum lazy load).
- WAV inference: `NEEDS_REVIEW`, `turbo`, `cuda`, 8 segments, 7.263 detik, hasil PASS.
- Hasil tersebut **tidak** mencakup keberhasilan konektivitas Laravel->GPU.

## Tahap berikutnya

1. Audit host .95 dan tentukan Laravel native vs containerized.
2. Konfigurasikan restricted SSH tunnel tanpa mengganti GPU API bind.
3. Verifikasi liveness, authenticated readiness dan test WAV dari lingkungan runtime Laravel.
4. Tambah Laravel Queue Job, retry policy, timeout, penyimpanan hasil, audit trail dan observability.
5. Uji satu alur end-to-end dengan rekaman uji yang diizinkan sebelum membuka layanan kepada pengguna.
