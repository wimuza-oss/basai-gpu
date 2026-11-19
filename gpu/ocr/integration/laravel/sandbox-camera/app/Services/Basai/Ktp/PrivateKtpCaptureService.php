<?php

declare(strict_types=1);

namespace App\Services\Basai\Ktp;

use Illuminate\Support\Facades\Storage;
use Illuminate\Support\Str;
use Illuminate\Validation\ValidationException;
use Throwable;

/**
 * Stores an original KTP only after GPU OCR returns reviewable fields.
 * The GPU never persists an image. This service has no SIPP database dependency.
 */
final class PrivateKtpCaptureService
{
    private const MAX_BYTES = 5 * 1024 * 1024;
    private const MAX_PIXELS = 16_000_000;

    /** @return array<string, mixed> */
    public function recognizeAndStore(#[\SensitiveParameter] string $base64, int $operatorId, GpuKtpOcrClient $ocr): array
    {
        $maxEncodedLength = 4 * intdiv(self::MAX_BYTES + 2, 3);
        if ($base64 === '' || strlen($base64) > $maxEncodedLength) {
            throw ValidationException::withMessages(['ktpImage' => 'Maksimum ukuran gambar adalah 5 MB.']);
        }

        $image = base64_decode($base64, true);
        if (! is_string($image) || $image === '' || strlen($image) > self::MAX_BYTES) {
            throw ValidationException::withMessages(['ktpImage' => 'Gambar KTP tidak valid atau terlalu besar.']);
        }

        $mime = (new \finfo(FILEINFO_MIME_TYPE))->buffer($image);
        $extension = match ($mime) {
            'image/jpeg' => 'jpg',
            'image/png' => 'png',
            default => null,
        };
        $info = @getimagesizefromstring($image);

        if ($extension === null || $info === false || ($info['mime'] ?? null) !== $mime ||
            $info[0] < 1 || $info[1] < 1 || $info[0] * $info[1] > self::MAX_PIXELS ||
            ! $this->isDecodable($image)) {
            throw ValidationException::withMessages(['ktpImage' => 'Gunakan JPEG/PNG valid maksimal 16 megapiksel.']);
        }

        $result = $ocr->read($image, $mime);

        if (($result['status'] ?? '') !== 'OCR_REVIEW' || empty($result['fields']) || ! is_array($result['fields'])) {
            return $result;
        }

        $disk = Storage::disk('local');
        $path = 'ktp-captures/'.Str::uuid();
        $original = "{$path}/original.{$extension}";
        $metadata = "{$path}/capture.json";
        $metadataJson = json_encode([
            'operator_id' => $operatorId,
            'mime' => $mime,
            'size_bytes' => strlen($image),
            'sha256' => hash('sha256', $image),
            'captured_at' => now()->toIso8601String(),
            'source' => 'basai-ktp-camera',
        ], JSON_THROW_ON_ERROR);

        try {
            $ok = $disk->put($original, $image, ['visibility' => 'private']) &&
                $disk->put($metadata, $metadataJson, ['visibility' => 'private']);
        } catch (Throwable) {
            $ok = false;
        }

        if (! $ok) {
            $disk->deleteDirectory($path);
            $result['status'] = 'STORAGE_ERROR';
            $result['warnings'] = ['Hasil OCR berhasil dibaca, tetapi penyimpanan privat gagal.'];
            return $result;
        }

        // Deliberately don't return image paths, storage identifiers, or sensitive metadata to the client.
        return $result;
    }

    private function isDecodable(string $image): bool
    {
        if (! function_exists('imagecreatefromstring')) {
            return false;
        }
        $resource = @imagecreatefromstring($image);
        if ($resource === false) {
            return false;
        }
        imagedestroy($resource);
        return true;
    }
}
