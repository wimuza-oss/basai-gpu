<div
    wire:ignore
    x-data="basaiKtpCamera()"
    x-on:basai-ktp-camera-result.window="acceptResult($event.detail.result)"
    class="panel panel-default basai-ktp-camera"
    style="margin-bottom:20px;"
>
    <div class="panel-heading">
        <div class="panel-title"><strong>Ambil Data KTP Saksi</strong> <small>— OCR GPU</small></div>
    </div>
    <div class="panel-body">
        <div class="form-group" style="display:flex;gap:6px;flex-wrap:wrap;">
            <button type="button" class="btn btn-default" @click="openCamera()" :disabled="busy || openingCamera">Buka Kamera</button>
            <button type="button" class="btn btn-primary" @click="takePhoto()" :disabled="busy || !stream">Ambil Foto</button>
            <button type="button" class="btn btn-default" @click="$refs.imagePicker.click()" :disabled="busy">Upload JPG/PNG</button>
            <input x-ref="imagePicker" type="file" accept="image/jpeg,image/png" hidden
                @change="selectFile($event.target.files[0]); $event.target.value=''">
        </div>
        <div class="form-group" x-show="stream" x-cloak>
            <video x-ref="camera" autoplay muted playsinline aria-label="Pratinjau kamera KTP"
                style="display:block;width:100%;max-height:380px;object-fit:contain;background:#222;"></video>
            <small class="text-muted">Penuhi frame dengan KTP, hindari pantulan cahaya, tunggu fokus stabil.</small>
        </div>
        <div class="form-group" x-show="preview" x-cloak>
            <img :src="preview || null" alt="Foto KTP sebelum OCR" style="display:block;max-width:100%;max-height:300px;object-fit:contain;">
        </div>
        <div class="form-group">
            <button type="button" class="btn btn-success" @click="recognize()" :disabled="busy || !file">Baca KTP (GPU)</button>
            <span role="status" aria-live="polite" x-text="status" style="margin-left:10px;"></span>
        </div>
        <div role="alert" x-show="warnings.length" x-cloak class="alert alert-warning" style="padding:10px;">
            <template x-for="(warning, index) in warnings" :key="index">
                <p x-text="warning" style="margin:0 0 4px;"></p>
            </template>
        </div>
        <p class="text-muted" x-show="hasResult" x-cloak>
            <strong x-text="complete ? 'Kolom prioritas lengkap, tetap periksa KTP.' : 'Hasil perlu diperiksa dan dilengkapi.'"></strong>
            <template x-if="missingLabels.length">
                <span> Belum terbaca: <span x-text="missingLabels.join(', ')"></span>.</span>
            </template>
        </p>
        <div class="row" x-show="hasResult" x-cloak>
            <template x-for="field in fieldDefinitions" :key="field.name">
                <div class="col-sm-6 form-group">
                    <label :for="'basai-ktp-field-' + field.name" x-text="field.label"></label>
                    <input class="form-control" type="text"
                        :id="'basai-ktp-field-' + field.name"
                        x-model="fields[field.name]" :inputmode="field.name === 'nik' ? 'numeric' : 'text'"
                        :maxlength="field.name === 'nik' ? 16 : 255" autocomplete="off">
                </div>
            </template>
        </div>
        <details x-show="hasResult" x-cloak>
            <summary>RAW OCR text (hanya pemeriksaan di browser)</summary>
            <pre x-text="rawText || 'Tidak ada teks dikenali.'" style="white-space:pre-wrap;overflow-wrap:anywhere;max-height:240px;overflow:auto;"></pre>
        </details>
        <div class="form-group" style="margin-top:12px;">
            <button class="btn btn-default" type="button" disabled title="Mapping data saksi SIPP belum disetujui">Submit ke SIPP — belum aktif</button>
        </div>
    </div>

    @script
    <script>
        Alpine.data('basaiKtpCamera', () => ({
            stream: null,
            openingCamera: false,
            cameraRequest: 0,
            file: null,
            preview: '',
            busy: false,
            hasResult: false,
            status: 'Pilih kamera atau upload KTP.',
            fields: {},
            rawText: '',
            warnings: [],
            missingLabels: [],
            complete: false,
            fieldDefinitions: [
                { name: 'nik', label: 'NIK' },
                { name: 'nama', label: 'Nama' },
                { name: 'tempat_lahir', label: 'Tempat Lahir' },
                { name: 'tanggal_lahir', label: 'Tanggal Lahir' },
                { name: 'jenis_kelamin', label: 'Jenis Kelamin' },
                { name: 'alamat', label: 'Alamat' },
                { name: 'rt_rw', label: 'RT/RW' },
                { name: 'kelurahan_desa', label: 'Kelurahan/Desa' },
                { name: 'kecamatan', label: 'Kecamatan' },
                { name: 'kabupaten_kota', label: 'Kabupaten/Kota' },
                { name: 'provinsi', label: 'Provinsi' },
                { name: 'agama', label: 'Agama' },
                { name: 'status_perkawinan', label: 'Status Perkawinan' },
                { name: 'pekerjaan', label: 'Pekerjaan' },
                { name: 'kewarganegaraan', label: 'Kewarganegaraan' },
                { name: 'berlaku_hingga', label: 'Berlaku Hingga' }
            ],

            destroy() {
                this.stopCamera();
                if (this.preview) URL.revokeObjectURL(this.preview);
            },
            stopCamera() {
                this.cameraRequest += 1;
                this.openingCamera = false;
                if (this.stream) this.stream.getTracks().forEach(track => track.stop());
                this.stream = null;
                if (this.$refs.camera) this.$refs.camera.srcObject = null;
            },
            async openCamera() {
                if (!navigator.mediaDevices?.getUserMedia) {
                    this.status = 'Browser tidak mengizinkan kamera. Gunakan HTTPS dan izinkan akses kamera.';
                    return;
                }
                this.stopCamera();
                const request = this.cameraRequest;
                this.openingCamera = true;
                try {
                    const stream = await navigator.mediaDevices.getUserMedia({
                        audio: false,
                        video: {
                            facingMode: { ideal: 'environment' },
                            width: { ideal: 2560 },
                            height: { ideal: 1440 }
                        }
                    });
                    if (this.cameraRequest !== request) {
                        stream.getTracks().forEach(track => track.stop());
                        return;
                    }
                    this.stream = stream;
                    this.$refs.camera.srcObject = stream;
                    const track = stream.getVideoTracks()[0];
                    if (track?.getCapabilities && track?.applyConstraints) {
                        const capabilities = track.getCapabilities();
                        if (Array.isArray(capabilities.focusMode) && capabilities.focusMode.includes('continuous')) {
                            try { await track.applyConstraints({ advanced: [{ focusMode: 'continuous' }] }); }
                            catch (_) { /* Tidak semua driver mendukung autofocus. */ }
                        }
                    }
                    this.status = 'Kamera aktif. Tunggu fokus, lalu klik Ambil Foto.';
                } catch (_) {
                    this.status = 'Kamera gagal dibuka. Periksa izin atau gunakan Upload JPG/PNG.';
                } finally {
                    if (this.cameraRequest === request) this.openingCamera = false;
                }
            },
            async takePhoto() {
                const video = this.$refs.camera;
                const track = this.stream?.getVideoTracks?.()[0];
                if (!track || !video?.videoWidth || !video?.videoHeight) {
                    this.status = 'Kamera belum siap.';
                    return;
                }
                this.status = 'Mengambil foto KTP…';
                await new Promise(resolve => setTimeout(resolve, 450));
                if (window.ImageCapture && this.stream) {
                    try {
                        const blob = await new ImageCapture(track).takePhoto();
                        if (blob && ['image/jpeg', 'image/png'].includes(blob.type)) {
                            this.selectFile(new File([blob], 'ktp-camera.' + (blob.type === 'image/png' ? 'png' : 'jpg'), { type: blob.type }));
                            return;
                        }
                    } catch (_) { /* Fallback ke frame video. */ }
                }
                const canvas = document.createElement('canvas');
                canvas.width = video.videoWidth;
                canvas.height = video.videoHeight;
                canvas.getContext('2d').drawImage(video, 0, 0);
                canvas.toBlob(blob => {
                    if (!blob) {
                        this.status = 'Foto gagal diambil.';
                        return;
                    }
                    this.selectFile(new File([blob], 'ktp-camera.jpg', { type: 'image/jpeg' }));
                }, 'image/jpeg', 0.98);
            },
            selectFile(file) {
                if (!file) return;
                this.stopCamera();
                if (this.preview) URL.revokeObjectURL(this.preview);
                this.preview = '';
                this.file = null;
                this.fields = {};
                this.rawText = '';
                this.warnings = [];
                this.missingLabels = [];
                this.hasResult = false;
                this.complete = false;
                if (!['image/jpeg', 'image/png'].includes(file.type) || file.size > 5 * 1024 * 1024 || file.size < 1) {
                    this.status = 'Gunakan JPG/PNG dengan ukuran maksimal 5 MB.';
                    return;
                }
                this.file = file;
                this.preview = URL.createObjectURL(file);
                this.status = 'Foto siap dibaca di GPU.';
            },
            async recognize() {
                if (!this.file || this.busy) return;
                this.busy = true;
                this.status = 'Memproses OCR pada GPU…';
                try {
                    const encoded = await new Promise((resolve, reject) => {
                        const reader = new FileReader();
                        reader.onload = () => resolve(String(reader.result).split(',')[1]);
                        reader.onerror = () => reject(reader.error);
                        reader.readAsDataURL(this.file);
                    });
                    await this.$wire.recognizeKtp(encoded);
                } catch (_) {
                    this.status = 'Permintaan OCR gagal. Periksa koneksi GPU.';
                } finally {
                    this.busy = false;
                }
            },
            acceptResult(result) {
                if (!result || typeof result !== 'object') return;
                this.fields = { ...result.fields };
                this.rawText = String(result.raw_text || '');
                this.warnings = Array.isArray(result.warnings) ? result.warnings : [];
                this.complete = result.required_complete === true;
                this.missingLabels = (result.missing_fields || []).map(name =>
                    this.fieldDefinitions.find(field => field.name === name)?.label || name
                );
                this.hasResult = result.status === 'OCR_REVIEW' || result.status === 'OCR_NO_FIELDS';
                this.status = {
                    OCR_REVIEW: 'OCR selesai. Periksa setiap kolom sebelum digunakan.',
                    OCR_NO_FIELDS: 'Belum ada kolom dikenali. Periksa teks OCR atau foto ulang.',
                    OCR_UNAVAILABLE: 'GPU OCR belum terhubung (periksa tunnel/token).',
                    OCR_FAILED: 'GPU tidak berhasil membaca gambar.',
                    INVALID_IMAGE: 'Gambar tidak valid.',
                    STORAGE_ERROR: 'OCR selesai tetapi gagal menyimpan gambar privat.'
                }[result.status] || 'OCR tidak berhasil.';
            }
        }));
    </script>
    @endscript
</div>
