#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime
from pathlib import Path
import shutil
import sys

ROOT = Path("/var/www/html/basai_tes")
ROUTES = ROOT / "routes" / "web.php"
VIEW = ROOT / "resources" / "views" / "basai" / "test-audio.blade.php"

OLD_GET = """Route::get(
    '/basai/test',
    [
        \\App\\Http\\Controllers\\Basai\\BasaiTestController::class,
        'show',
    ]
)->name('basai.test.show');"""

NEW_GET = """Route::get(
    '/basai/test',
    [
        \\App\\Http\\Controllers\\Basai\\BasaiTestController::class,
        'show',
    ]
)
    ->middleware(\\App\\Http\\Middleware\\RequireBasaiAuthentication::class)
    ->name('basai.test.show');"""

OLD_POST = """Route::post(
    '/basai/test',
    [
        \\App\\Http\\Controllers\\Basai\\BasaiTestController::class,
        'transcribe',
    ]
)->name('basai.test.transcribe');"""

NEW_POST = """Route::post(
    '/basai/test',
    [
        \\App\\Http\\Controllers\\Basai\\BasaiTestController::class,
        'transcribe',
    ]
)
    ->middleware(\\App\\Http\\Middleware\\RequireBasaiAuthentication::class)
    ->name('basai.test.transcribe');"""

VIEW_MARKER = """<body>

<h1>BAS-AI — Test Audio</h1>"""

VIEW_REPLACEMENT = """<body>

@include('auth.basai-userbar')

<h1>BAS-AI — Test Audio</h1>"""


def replace_exact(source: str, old: str, new: str, label: str) -> str:
    if new in source:
        return source
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly 1 live block, found {count}")
    return source.replace(old, new, 1)


def main() -> int:
    if not ROUTES.is_file() or not VIEW.is_file():
        raise RuntimeError("Live route/view file not found")

    routes = ROUTES.read_text(encoding="utf-8")
    view = VIEW.read_text(encoding="utf-8")

    patched_routes = replace_exact(routes, OLD_GET, NEW_GET, "GET route")
    patched_routes = replace_exact(patched_routes, OLD_POST, NEW_POST, "POST route")
    patched_view = replace_exact(view, VIEW_MARKER, VIEW_REPLACEMENT, "test-audio view")

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = ROOT / ".basai-backup" / f"d5h-live-{stamp}"
    backup.mkdir(parents=True, exist_ok=False)

    shutil.copy2(ROUTES, backup / "web.php")
    shutil.copy2(VIEW, backup / "test-audio.blade.php")

    ROUTES.write_text(patched_routes, encoding="utf-8")
    VIEW.write_text(patched_view, encoding="utf-8")

    print("D5H_LIVE_APPLIED=YES")
    print(f"BACKUP={backup}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print("D5H_LIVE_APPLIED=NO")
        print(f"ERROR={exc}", file=sys.stderr)
        raise SystemExit(1)
