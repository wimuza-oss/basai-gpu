#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = Path("/var/www/html/basai_tes")
ROUTES = ROOT / "routes" / "web.php"
SOURCE_CLASS = ROOT / "app" / "Livewire" / "BasAiAssistant.php"
TARGET_CLASS = ROOT / "app" / "Livewire" / "BasAiTestAssistant.php"
SOURCE_VIEW = ROOT / "resources" / "views" / "livewire" / "bas-ai-assistant.blade.php"
TARGET_VIEW = ROOT / "resources" / "views" / "livewire" / "bas-ai-test-assistant.blade.php"

ROUTE_RE = re.compile(
    r"Route::get\(\s*['\"]/basai/test['\"]\s*,.*?"
    r"->name\(\s*['\"]basai\.test\.show['\"]\s*\)\s*;",
    re.DOTALL,
)

NEW_ROUTE = """Route::get(
    '/basai/test',
    \\App\\Livewire\\BasAiTestAssistant::class
)
    ->middleware(\\App\\Http\\Middleware\\RequireBasaiAuthentication::class)
    ->name('basai.test.show');"""


def fail(message: str) -> None:
    raise RuntimeError(message)


def atomic_write(path: Path, content: str, mode_from: Path | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
    tmp = Path(tmp_name)
    try:
        with open(fd, "w", encoding="utf-8", closefd=True) as stream:
            stream.write(content)
            stream.flush()
        if mode_from and mode_from.exists():
            shutil.copymode(mode_from, tmp)
        tmp.replace(path)
    finally:
        if tmp.exists():
            tmp.unlink()


def clone_class(source: str) -> str:
    if source.count("class BasAiAssistant") != 1:
        fail("Deklarasi class BasAiAssistant tidak ditemukan tepat satu kali.")

    cloned = source.replace("class BasAiAssistant", "class BasAiTestAssistant", 1)

    if "livewire.bas-ai-assistant" not in cloned:
        fail("View livewire.bas-ai-assistant tidak ditemukan pada class sumber.")
    cloned = cloned.replace("livewire.bas-ai-assistant", "livewire.bas-ai-test-assistant")

    stage_pattern = re.compile(
        r"(#\[Url\(\s*as:\s*['\"]tahap['\"]\s*,\s*except:\s*)0(\s*\)\]\s*"
        r"public\s+int\s+\$[A-Za-z_][A-Za-z0-9_]*\s*=\s*)0(\s*;)"
    )
    matches = list(stage_pattern.finditer(cloned))
    if len(matches) != 1:
        fail(
            "Default tahap Livewire tidak dikenali secara aman; "
            f"ditemukan {len(matches)} pola."
        )
    cloned = stage_pattern.sub(r"\g<1>1\g<2>1\g<3>", cloned, count=1)

    return cloned


def patch_routes(source: str) -> str:
    matches = list(ROUTE_RE.finditer(source))
    if len(matches) != 1:
        fail(
            "Route basai.test.show harus ditemukan tepat satu kali; "
            f"ditemukan {len(matches)}."
        )
    return source[:matches[0].start()] + NEW_ROUTE + source[matches[0].end():]


def php_lint(path: Path) -> tuple[bool, str]:
    result = subprocess.run(
        ["php", "-l", str(path)],
        text=True,
        capture_output=True,
        check=False,
    )
    output = (result.stdout + result.stderr).strip()
    return result.returncode == 0, output


def main() -> int:
    for path in (ROUTES, SOURCE_CLASS, SOURCE_VIEW):
        if not path.is_file():
            fail(f"Source live tidak ditemukan: {path}")
        if path.is_symlink():
            fail(f"Source live tidak boleh symlink: {path}")

    routes_original = ROUTES.read_text(encoding="utf-8")
    class_original = SOURCE_CLASS.read_text(encoding="utf-8")
    view_original = SOURCE_VIEW.read_text(encoding="utf-8")

    class_cloned = clone_class(class_original)
    routes_patched = patch_routes(routes_original)

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = ROOT / ".basai-backup" / f"clone-ui-test-{stamp}"
    backup.mkdir(parents=True, exist_ok=False)

    shutil.copy2(ROUTES, backup / "web.php")
    if TARGET_CLASS.exists():
        shutil.copy2(TARGET_CLASS, backup / TARGET_CLASS.name)
    if TARGET_VIEW.exists():
        shutil.copy2(TARGET_VIEW, backup / TARGET_VIEW.name)

    try:
        atomic_write(TARGET_CLASS, class_cloned, SOURCE_CLASS)
        atomic_write(TARGET_VIEW, view_original, SOURCE_VIEW)
        atomic_write(ROUTES, routes_patched, ROUTES)

        for path in (TARGET_CLASS, ROUTES):
            ok, output = php_lint(path)
            print(output)
            if not ok:
                fail(f"PHP lint gagal: {path}")

    except Exception:
        shutil.copy2(backup / "web.php", ROUTES)

        class_backup = backup / TARGET_CLASS.name
        view_backup = backup / TARGET_VIEW.name

        if class_backup.exists():
            shutil.copy2(class_backup, TARGET_CLASS)
        elif TARGET_CLASS.exists():
            TARGET_CLASS.unlink()

        if view_backup.exists():
            shutil.copy2(view_backup, TARGET_VIEW)
        elif TARGET_VIEW.exists():
            TARGET_VIEW.unlink()
        raise

    print("CLONE_APPLIED=YES")
    print(f"BACKUP={backup}")
    print(f"TEST_CLASS={TARGET_CLASS}")
    print(f"TEST_VIEW={TARGET_VIEW}")
    print("TEST_URL=/basai/test")
    print("SOURCE_MAIN_UNCHANGED=YES")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print("CLONE_APPLIED=NO")
        print(f"ERROR={exc}", file=sys.stderr)
        raise SystemExit(1)
