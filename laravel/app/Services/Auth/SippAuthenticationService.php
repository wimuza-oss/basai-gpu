<?php

declare(strict_types=1);

namespace App\Services\Auth;

use App\Data\Auth\SippUserData;
use App\Exceptions\SippAuthenticationException;
use Illuminate\Database\QueryException;
use Illuminate\Support\Facades\DB;

final class SippAuthenticationService
{
    public function authenticate(string $username, string $plainPassword): ?SippUserData
    {
        $username = trim($username);

        if ($username === '' || $plainPassword === '') {
            return null;
        }

        try {
            $rows = DB::connection('mysql')->select(
                'CALL basai_autentikasi_sipp(?, ?)',
                [$username, md5($plainPassword)]
            );
        } catch (QueryException $exception) {
            report($exception);

            throw new SippAuthenticationException(
                'Layanan autentikasi SIPP tidak dapat diakses.',
                previous: $exception,
            );
        }

        if ($rows === []) {
            return null;
        }

        return SippUserData::fromDatabaseRow($rows[0]);
    }
}
