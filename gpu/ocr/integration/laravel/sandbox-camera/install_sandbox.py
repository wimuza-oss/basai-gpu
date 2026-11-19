#!/usr/bin/env python3
"""Install a self-contained KTP Livewire camera panel in the BAS-AI sandbox only.

Never edits production component, shared layout, routes, .env or GPU services.
Backs up every overwritten file and refuses to patch a view of unknown shape.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import grp
import hashlib
import json
import os
from pathlib import Path
import pwd
import re
import shutil
import subprocess
import sys
import tempfile

MODULE_FILES = (
    "app/Contracts/Basai/KtpOcrService.php",
    "app/Services/Basai/Ktp/GpuKtpOcrClient.php",
    "app/Services/Basai/Ktp/PrivateKtpCaptureService.php",
    "app/Livewire/Basai/KtpCamera.php",
    "config/basai_ocr.php",
    "resources/views/livewire/basai/ktp-camera.blade.php",
)
SHARED_CORE_FILES = (
    "app/Contracts/Basai/KtpOcrService.php",
    "app/Services/Basai/Ktp/GpuKtpOcrClient.php",
    "config/basai_ocr.php",
)
PARENT_VIEW = "resources/views/livewire/bas-ai-test-assistant.blade.php"
TEAM_FILES = (
    "app/Livewire/BasAiAssistant.php",
    "resources/views/livewire/bas-ai-assistant.blade.php",
    "resources/views/components/layouts/app.blade.php",
)
INCLUDE = "                <livewire:basai.ktp-camera />\n\n"
ANCHOR = re.compile(
    r'(?m)^ {16}<div class="panel panel-default">\s*'
    r'<div class="panel-heading">\s*'
    r'<div class="panel-title"><strong>Rekaman Sidang</strong>',
)
OLD_PANEL = re.compile(r'(?m)^ {16}<div class="panel panel-default"[^>]*x-data="basKtpCapture\(\)"')


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read(path: Path) -> bytes:
    if not path.is_file() or path.is_symlink():
        raise RuntimeError(f"Berkas tidak ada atau symlink tidak aman: {path}")
    return path.read_bytes()


def ensure_under_root(root: Path, relative: str) -> Path:
    target = root / relative
    for parent in (target, *target.parents):
        if parent == root.parent:
            break
        if parent.is_symlink():
            raise RuntimeError(f"STOP: ditemukan symlink pada lokasi target: {parent}")
    return target


def write_atomic(dest: Path, content: bytes, *, owner: tuple[int, int] | None, mode: int = 0o644) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".basai-ktp-", dir=dest.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, mode)
        if owner is not None and os.geteuid() == 0:
            os.chown(temporary, *owner)
        os.replace(temporary, dest)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def install_view(view: bytes) -> bytes:
    text = view.decode("utf-8")
    if "<livewire:basai.ktp-camera" in text:
        if text.count("<livewire:basai.ktp-camera") != 1:
            raise RuntimeError("STOP: duplikasi komponen KTP di Blade clone.")
        return view

    matches = list(ANCHOR.finditer(text))
    if len(matches) != 1:
        raise RuntimeError("STOP: panel 'Rekaman Sidang' tidak unik; tidak berani memodifikasi Blade.")
    anchor = matches[0]
    old = list(OLD_PANEL.finditer(text[:anchor.start()]))
    if len(old) > 1:
        raise RuntimeError("STOP: ditemukan beberapa panel lama KTP; perlu audit manual.")
    if old:
        start = old[0].start()
        block = text[start:anchor.start()]
        required = ("Ambil Data KTP Saksi", "Buka Kamera", "Submit ke SIPP")
        if not all(token in block for token in required):
            raise RuntimeError("STOP: panel KTP lama tidak cocok dengan struktur terverifikasi.")
        return (text[:start] + INCLUDE + text[anchor.start():]).encode("utf-8")

    if "Ambil Data KTP Saksi" in text or "basai.sandbox.ktp-capture" in text:
        raise RuntimeError("STOP: ada modul KTP lain di clone. Hindari duplikasi, audit dahulu.")
    return (text[:anchor.start()] + INCLUDE + text[anchor.start():]).encode("utf-8")


def check_route(root: Path) -> None:
    route_file = read(root / "routes/web.php").decode("utf-8")
    if not re.search(r"Route::get\(\s*['\"]/basai/test['\"]\s*,\s*(?:\\App\\Livewire\\)?BasAiTestAssistant::class", route_file):
        raise RuntimeError("STOP: route GET /basai/test tidak menuju clone BasAiTestAssistant. Jangan pasang di halaman tim.")
    command = ["php", "artisan", "route:list", "--path=basai/test", "--json"]
    if os.geteuid() == 0:
        command = ["sudo", "-u", "www-data", *command]
    result = subprocess.run(command, cwd=root, capture_output=True, text=True, timeout=50, check=False)
    if result.returncode != 0:
        raise RuntimeError("STOP: gagal audit route Laravel (periksa command PHP/permission).")
    try:
        routes = json.loads(result.stdout)
        matching = [route for route in routes if
                    "GET" in str(route.get("method", "")) and
                    str(route.get("uri", "")).strip("/") == "basai/test"]
        if len(matching) != 1 or "BasAiTestAssistant" not in str(matching[0].get("action", "")):
            raise ValueError("target bukan clone")
    except (ValueError, TypeError) as exc:
        raise RuntimeError("STOP: runtime route /basai/test tidak mengarah ke clone.") from exc


def php_lint(files: list[Path]) -> None:
    for path in files:
        result = subprocess.run(["php", "-l", str(path)], capture_output=True, text=True, timeout=20)
        if result.returncode != 0:
            raise RuntimeError(f"STOP: PHP lint gagal untuk {path.name}: {result.stderr.strip()}")


def install(root: Path, source: Path, *, skip_runtime_route: bool = False) -> str:
    if not root.is_dir() or not (root / "artisan").exists():
        raise RuntimeError("STOP: direktori Laravel target tidak valid.")
    if not source.is_dir():
        raise RuntimeError("STOP: sumber modul tidak ada.")

    for relative in TEAM_FILES:
        read(root / relative)
    protected_before = {p: digest(read(root / p)) for p in TEAM_FILES}

    if not skip_runtime_route:
        check_route(root)

    parent = ensure_under_root(root, PARENT_VIEW)
    parent_old = read(parent)
    parent_new = install_view(parent_old)

    payload: dict[str, bytes] = {}
    resolved_sources = {}
    for relative in MODULE_FILES:
        src = source / relative
        if not src.is_file() and relative in SHARED_CORE_FILES:
            src = source.parent / relative
        resolved_sources[relative] = src
        payload[relative] = read(src)
    payload[PARENT_VIEW] = parent_new

    php_lint([resolved_sources[p] for p in MODULE_FILES if p.endswith(".php")])

    changed = [p for p, contents in payload.items()
               if not (root / p).is_file() or read(root / p) != contents]
    if not changed:
        return "SUDAH_TERPASANG (tanpa perubahan)"

    label = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = root / ".basai-backup" / f"ktp-camera-{label}"
    backup.mkdir(parents=True, exist_ok=False)
    os.chmod(backup, 0o750)
    inventory: list[dict[str, str | bool]] = []
    newfiles: list[Path] = []
    try:
        try:
            user = pwd.getpwnam("ngadimin").pw_uid
            group = grp.getgrnam("www-data").gr_gid
            default_owner = (user, group)
        except KeyError:
            default_owner = None

        for relative in changed:
            target = ensure_under_root(root, relative)
            old_exists = target.is_file()
            old_content = read(target) if old_exists else b""
            if old_exists:
                copy = backup / relative
                copy.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(target, copy)
            else:
                newfiles.append(target)

            if old_exists:
                info = target.stat()
                owner = (info.st_uid, info.st_gid)
                mode = info.st_mode & 0o777
            else:
                owner = default_owner
                mode = 0o644
            write_atomic(target, payload[relative], owner=owner, mode=mode)
            inventory.append({
                "path": relative,
                "existed": old_exists,
                "before_sha256": digest(old_content) if old_exists else "",
                "deployed_sha256": digest(payload[relative]),
            })

        php_lint([root / p for p in changed if p.endswith(".php")])
        protected_after = {p: digest(read(root / p)) for p in TEAM_FILES}
        if protected_after != protected_before:
            raise RuntimeError("STOP: hash source tim berubah, rollback segera.")

        manifest = {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "changed": inventory,
            "protected_sha256": protected_before,
            "module_version": "ktp-camera-1.0.0",
        }
        (backup / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        os.chmod(backup / "manifest.json", 0o640)
    except BaseException:
        # Full transaction rollback, preserving original file ownership/permissions.
        for record in reversed(inventory):
            path = root / str(record["path"])
            if record["existed"]:
                shutil.copy2(backup / str(record["path"]), path)
            elif path.exists():
                path.unlink()
        for path in newfiles:
            if path.exists() and not any(rec["path"] == str(path.relative_to(root)) for rec in inventory):
                path.unlink()
        raise
    return f"TERPASANG backup={backup} files={len(changed)}"


def rollback(root: Path, backup: Path) -> str:
    manifest = json.loads(read(backup / "manifest.json"))
    for relative in TEAM_FILES:
        current = digest(read(root / relative))
        if current != manifest["protected_sha256"][relative]:
            raise RuntimeError("STOP: source tim berubah sesudah deployment; audit sebelum rollback.")
    for rec in manifest["changed"]:
        path = ensure_under_root(root, rec["path"])
        if not path.is_file() or digest(read(path)) != rec["deployed_sha256"]:
            raise RuntimeError("STOP: modul telah diubah setelah install; rollback otomatis tidak aman.")
    for rec in manifest["changed"]:
        path = root / rec["path"]
        if rec["existed"]:
            shutil.copy2(backup / rec["path"], path)
        else:
            path.unlink()
    return "ROLLBACK_SELESAI"


def main() -> int:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--root", default="/var/www/html/basai_tes")
    cli.add_argument("--source", default=str(Path(__file__).resolve().parent))
    cli.add_argument("--rollback", metavar="BACKUP_DIR")
    args = cli.parse_args()
    root = Path(args.root).resolve()
    try:
        if args.rollback:
            print(rollback(root, Path(args.rollback).resolve()))
        else:
            # The route runtime check is mandatory for actual deployment.
            print(install(root, Path(args.source).resolve()))
            print("NEXT: isi BASAI_OCR_URL/TOKEN pada .env lokal, verifikasi tunnel, dan compile views.")
        return 0
    except (RuntimeError, OSError, subprocess.TimeoutExpired) as error:
        print(f"GAGAL: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
