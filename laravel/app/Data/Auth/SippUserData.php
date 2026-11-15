<?php

declare(strict_types=1);

namespace App\Data\Auth;

final readonly class SippUserData
{
    public function __construct(
        public int $userid,
        public string $fullname,
        public string $username,
        public bool $adminBasai,
    ) {
    }

    /**
     * @param object{userid:mixed, fullname:mixed, username:mixed, admin_basai:mixed} $row
     */
    public static function fromDatabaseRow(object $row): self
    {
        return new self(
            userid: (int) $row->userid,
            fullname: trim((string) $row->fullname),
            username: trim((string) $row->username),
            adminBasai: (int) $row->admin_basai === 1,
        );
    }
}
