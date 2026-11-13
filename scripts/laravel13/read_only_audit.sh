#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${1:-/var/www/html/basai_tes}"

fail() { printf 'FAIL: %s\n' "$*" >&2; exit 1; }
section() { printf '\n===== %s =====\n' "$1"; }

[ -d "$APP_DIR" ] || fail "Direktori aplikasi tidak ditemukan: $APP_DIR"
cd "$APP_DIR"

[ -f artisan ] || fail "artisan tidak ditemukan di $APP_DIR"
[ -f config/basai.php ] || fail "config/basai.php tidak ditemukan"

section "IDENTITAS APLIKASI"
printf 'app_dir=%s\n' "$APP_DIR"
php artisan --version
php -r 'printf("php=%s\n", PHP_VERSION);'

section "VALIDASI FILE KONFIGURASI"
php -l config/basai.php
php -l config/filesystems.php
printf 'config_cache_file=%s\n' "$([ -f bootstrap/cache/config.php ] && echo present || echo absent)"

section "KONFIGURASI BASAI MELALUI BOOTSTRAP LARAVEL"
php artisan tinker --execute='
$p = config("basai.pipeline");
dump([
    "configuration_cached" => app()->configurationIsCached(),
    "basai_loaded" => config()->has("basai"),
    "pipeline_loaded" => config()->has("basai.pipeline"),
    "pipeline_type" => get_debug_type($p),
    "pipeline_keys" => is_array($p) ? array_keys($p) : null,
    "work_directory" => is_array($p) ? ($p["work_directory"] ?? null) : null,
    "max_source_bytes" => is_array($p) ? ($p["max_source_bytes"] ?? null) : null,
    "source_disks" => is_array($p) ? ($p["source_disks"] ?? null) : null,
]);'

section "DISK BASAI_ORIGINALS MELALUI BOOTSTRAP LARAVEL"
php artisan tinker --execute='
$d = config("filesystems.disks.basai_originals");
dump([
    "disk_loaded" => is_array($d),
    "driver" => is_array($d) ? ($d["driver"] ?? null) : null,
    "root" => is_array($d) ? ($d["root"] ?? null) : null,
    "visibility" => is_array($d) ? ($d["visibility"] ?? null) : null,
    "throw" => is_array($d) ? ($d["throw"] ?? null) : null,
]);'

section "SUMBER KONFIGURASI YANG RELEVAN"
grep -nE "pipeline|work_directory|max_source_bytes|source_disks" config/basai.php || true
grep -nE "basai_originals" config/filesystems.php || true

section "LARAVELDISKAUDIOSOURCE"
SOURCE_FILE="app/Services/Basai/Pipeline/LaravelDiskAudioSource.php"
if [ -f "$SOURCE_FILE" ]; then
    php -l "$SOURCE_FILE"
    grep -nE "source_disks|Storage::disk|readStream|disk|Invalid|allow" "$SOURCE_FILE" || true
else
    printf 'missing=%s\n' "$SOURCE_FILE"
fi

section "REFERENSI BASAI_ORIGINALS / PIPELINE"
grep -RIn --exclude-dir=vendor --exclude-dir=node_modules --exclude='.env' \
    -E "basai_originals|basai\.pipeline|LaravelDiskAudioSource" \
    app config routes tests 2>/dev/null || true

section "FFMPEG"
if command -v ffmpeg >/dev/null 2>&1; then
    printf 'ffmpeg=%s\n' "$(command -v ffmpeg)"
    ffmpeg -version | head -n 1
else
    printf 'ffmpeg=NOT_FOUND\n'
fi

section "DIREKTORI PIPELINE"
for p in /var/lib/basai-tes /var/lib/basai-tes/originals /var/lib/basai-tes/work; do
    if [ -e "$p" ]; then
        stat -c '%A %U:%G %n' "$p"
    else
        printf 'missing=%s\n' "$p"
    fi
done

section "KESIMPULAN OTOMATIS"
php artisan tinker --execute='
$p = config("basai.pipeline");
$disk = config("filesystems.disks.basai_originals");
$errors = [];
if (!is_array($p)) $errors[] = "basai.pipeline tidak termuat sebagai array";
if (is_array($p) && !in_array("basai_originals", $p["source_disks"] ?? [], true)) {
    $errors[] = "basai_originals tidak ada dalam basai.pipeline.source_disks";
}
if (!is_array($disk)) $errors[] = "filesystems.disks.basai_originals tidak termuat";
dump(["ok" => $errors === [], "errors" => $errors]);'

printf '\nAUDIT READ-ONLY SELESAI. Tidak ada file yang diubah.\n'
