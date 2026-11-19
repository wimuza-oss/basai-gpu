<?php

declare(strict_types=1);

namespace App\Contracts\Basai;

interface KtpOcrService
{
    /** @return array<string, mixed> */
    public function read(string $image, string $mime): array;
}
