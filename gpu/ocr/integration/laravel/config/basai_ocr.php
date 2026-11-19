<?php

declare(strict_types=1);

return [
    'url' => env('BASAI_OCR_URL', 'http://127.0.0.1:18169'),
    'token' => env('BASAI_OCR_TOKEN', ''),
    'connect_timeout' => (int) env('BASAI_OCR_CONNECT_TIMEOUT', 5),
    'timeout' => (int) env('BASAI_OCR_TIMEOUT', 90),
];
