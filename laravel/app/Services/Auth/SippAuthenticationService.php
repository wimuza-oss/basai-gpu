<?php

declare(strict_types=1);

namespace App\Services\Auth;

use App\Data\Auth\SippUserData;
use App\Exceptions\SippAuthenticationException;
use Illuminate\Database\QueryException;
use Illuminate\Support\Facades\DB;
use PDO;
use PDOException;
use PDOStatement;
use Throwable;

final class SippAuthenticationService
{
    public function authenticate(string $username, string $plainPassword): ?SippUserData
    {
        $username = trim($username);

        if ($username === '' || $plainPassword === '') {
            return null;
        }

        $statement = null;

        try {
            $pdo = DB::connection('mysql')->getPdo();

            $statement = $pdo->prepare(
                'CALL basai_autentikasi_sipp(:username, :password_md5)'
            );

            $statement->execute([
                'username' => $username,
                'password_md5' => md5($plainPassword),
            ]);

            $row = $statement->fetch(PDO::FETCH_OBJ);

            $this->drainResultSets($statement);

            if ($row === false) {
                return null;
            }

            return SippUserData::fromDatabaseRow($row);
        } catch (PDOException|QueryException $exception) {
            report($exception);

            throw new SippAuthenticationException(
                'Layanan autentikasi SIPP tidak dapat diakses.',
                previous: $exception,
            );
        } catch (Throwable $exception) {
            report($exception);

            throw new SippAuthenticationException(
                'Terjadi kegagalan saat memproses autentikasi SIPP.',
                previous: $exception,
            );
        } finally {
            if ($statement instanceof PDOStatement) {
                try {
                    $statement->closeCursor();
                } catch (Throwable) {
                    // Cursor cleanup must not replace the original auth result/error.
                }
            }
        }
    }

    private function drainResultSets(PDOStatement $statement): void
    {
        while ($statement->nextRowset()) {
            // MariaDB CALL may return additional empty result sets.
        }
    }
}
