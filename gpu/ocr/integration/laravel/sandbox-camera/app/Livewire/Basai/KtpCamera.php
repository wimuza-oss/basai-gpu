<?php

declare(strict_types=1);

namespace App\Livewire\Basai;

use App\Services\Basai\Ktp\GpuKtpOcrClient;
use App\Services\Basai\Ktp\PrivateKtpCaptureService;
use Illuminate\Validation\ValidationException;
use Livewire\Component;

/**
 * Independent KTP capture panel. No SIPP writes and no dependency on the main BAS-AI component.
 */
final class KtpCamera extends Component
{
    public function recognizeKtp(
        #[\SensitiveParameter] string $encodedImage,
        GpuKtpOcrClient $ocr,
        PrivateKtpCaptureService $captures,
    ): void {
        $auth = session('basai.auth', []);

        abort_unless(is_array($auth) && ! empty($auth['username']), 403);

        $userId = filter_var(
            $auth['userid'] ?? null,
            FILTER_VALIDATE_INT,
            ['options' => ['min_range' => 1]],
        );
        abort_if($userId === false, 403);

        try {
            $result = $captures->recognizeAndStore($encodedImage, (int) $userId, $ocr);
        } catch (ValidationException $exception) {
            $message = $exception->errors()['ktpImage'][0] ?? 'Gambar KTP tidak valid.';
            $this->dispatch('basai-ktp-camera-result', result: [
                'status' => 'INVALID_IMAGE',
                'fields' => [],
                'raw_text' => '',
                'warnings' => [$message],
            ]);

            return;
        }

        $this->dispatch('basai-ktp-camera-result', result: $result);
    }

    public function render(): \Illuminate\Contracts\View\View
    {
        return view('livewire.basai.ktp-camera');
    }
}
