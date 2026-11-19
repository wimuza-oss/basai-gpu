<?php

declare(strict_types=1);

namespace App\Services\Basai\Test;

use App\Services\Basai\Ktp\GpuKtpOcrClient;

/** Compatibility adapter untuk KtpCaptureService sandbox yang sudah ada. */
final class GpuKtpOcrService implements KtpOcrService
{
    public function __construct(private readonly GpuKtpOcrClient $client) {}

    /** @return array<string, mixed> */
    public function read(string $image, string $mime): array
    {
        return $this->client->read($image, $mime);
    }
}
