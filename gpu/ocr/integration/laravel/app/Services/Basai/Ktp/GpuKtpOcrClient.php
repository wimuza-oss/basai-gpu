<?php

declare(strict_types=1);

namespace App\Services\Basai\Ktp;

use App\Contracts\Basai\KtpOcrService;

use Illuminate\Support\Facades\Http;
use Throwable;

/**
 * HTTP client reusable di sandbox dan halaman produksi.
 * Semua OCR dan parsing terjadi di GPU, bukan di Livewire.
 */
final class GpuKtpOcrClient implements KtpOcrService
{
    private const REQUIRED_FIELDS = [
        'nik', 'nama', 'tempat_lahir', 'tanggal_lahir', 'alamat',
        'kelurahan_desa', 'kecamatan', 'kabupaten_kota', 'provinsi',
        'agama', 'pekerjaan',
    ];

    /** @return array{status: string, fields: array<string, string>, raw_text: string, warnings?: array, field_confidences?: array} */
    public function read(string $image, string $mime): array
    {
        $url = rtrim((string) config('basai_ocr.url', ''), '/');
        $token = (string) config('basai_ocr.token', '');

        if ($url === '' || strlen($token) < 32) {
            return $this->failed('OCR_UNAVAILABLE');
        }

        // Endpoint dibatasi ke loopback; SSH tunnel mengenkripsi trafik antarserver.
        $host = parse_url($url, PHP_URL_HOST);
        if (!in_array($host, ['localhost', '127.0.0.1', '::1'], true)) {
            return $this->failed('OCR_UNAVAILABLE');
        }

        if (! in_array($mime, ['image/png', 'image/jpeg'], true)) {
            return $this->failed('OCR_FAILED');
        }

        try {
            $response = Http::withToken($token)
                ->acceptJson()
                ->connectTimeout((int) config('basai_ocr.connect_timeout', 5))
                ->timeout((int) config('basai_ocr.timeout', 90))
                ->withOptions(['allow_redirects' => false])
                ->attach('image', $image, $mime === 'image/png' ? 'ktp.png' : 'ktp.jpg', ['Content-Type' => $mime])
                ->post($url.'/v1/ktp/ocr');
        } catch (Throwable) {
            // Jangan report exception HTTP yang dapat menyertakan payload/metadata sensitif.
            return $this->failed('OCR_UNAVAILABLE');
        }

        if (! $response->successful()) {
            return $this->failed('OCR_FAILED');
        }

        $data = $response->json();
        if (! is_array($data)) {
            return $this->failed('OCR_FAILED');
        }

        $status = (string) ($data['status'] ?? 'OCR_FAILED');
        if (! in_array($status, ['OCR_REVIEW', 'OCR_NO_FIELDS'], true)) {
            return $this->failed('OCR_FAILED');
        }

        $fields = [];
        $allowed = [
            'nik', 'nama', 'tempat_lahir', 'tanggal_lahir', 'jenis_kelamin',
            'alamat', 'rt_rw', 'kelurahan_desa', 'kecamatan',
            'kabupaten_kota', 'provinsi', 'agama',
            'status_perkawinan', 'pekerjaan', 'kewarganegaraan', 'berlaku_hingga',
        ];
        foreach ($allowed as $field) {
            $value = $data['fields'][$field] ?? null;
            if (is_string($value) && trim($value) !== '') {
                $fields[$field] = mb_substr(trim($value), 0, $field === 'nik' ? 16 : 255);
            }
        }
        if (isset($fields['nik']) && !preg_match('/^[0-9]{16}$/D', $fields['nik'])) {
            unset($fields['nik']);
        }

        $missingFields = array_values(array_filter(
            self::REQUIRED_FIELDS,
            static fn (string $key): bool => ! isset($fields[$key])
        ));

        return [
            'status' => $fields === [] ? 'OCR_NO_FIELDS' : 'OCR_REVIEW',
            'fields' => $fields,
            'raw_text' => is_string($data['raw_text'] ?? null) ? mb_substr($data['raw_text'], 0, 20000) : '',
            'warnings' => is_array($data['warnings'] ?? null) ? $data['warnings'] : [],
            'field_confidences' => is_array($data['field_confidences'] ?? null) ? $data['field_confidences'] : [],
            'required_fields' => self::REQUIRED_FIELDS,
            'missing_fields' => $missingFields,
            'required_complete' => $missingFields === [],
            'review_required' => true,
        ];
    }

    /** @return array{status: string, fields: array, raw_text: string} */
    private function failed(string $status): array
    {
        return [
            'status' => $status,
            'fields' => [],
            'raw_text' => '',
            'required_fields' => self::REQUIRED_FIELDS,
            'missing_fields' => self::REQUIRED_FIELDS,
            'required_complete' => false,
        ];
    }
}
