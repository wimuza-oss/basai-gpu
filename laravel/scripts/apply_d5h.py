#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
import re
import shutil
import sys


MIDDLEWARE = r"\App\Http\Middleware\RequireBasaiAuthentication::class"
INCLUDE = "@include('auth.basai-userbar')"
ROUTE_NAMES = ("basai.test.show", "basai.test.transcribe")


def fail(message: str) -> None:
    raise RuntimeError(message)


def patch_named_route(source: str, route_name: str) -> str:
    name_pattern = re.compile(
        r"->name\(\s*(['\"])" + re.escape(route_name) + r"\1\s*\)"
    )
    matches = list(name_pattern.finditer(source))
    if len(matches) != 1:
        fail(f"Route {route_name!r} harus ditemukan tepat satu kali; ditemukan {len(matches)}.")

    match = matches[0]
    surrounding = source[max(0, match.start() - 500): min(len(source), match.end() + 500)]
    if "RequireBasaiAuthentication::class" in surrounding:
        return source

    replacement = match.group(0) + "\n    ->middleware(" + MIDDLEWARE + ")"
    return source[:match.start()] + replacement + source[match.end():]


def discover_view(controller: Path, root: Path) -> Path:
    source = controller.read_text(encoding="utf-8")
    candidates = re.findall(r"\bview\(\s*(['\"])([^'\"]+)\1", source)
    names = [name for _, name in candidates]

    if not names:
        fail("Tidak menemukan pemanggilan view() pada BasaiTestController.")

    preferred = [name for name in names if "test" in name.lower()]
    view_name = preferred[0] if preferred else names[0]
    path = root / "resources" / "views" / (view_name.replace(".", "/") + ".blade.php")

    if not path.is_file():
        fail(f"Blade hasil discovery tidak ditemukan: {path}")

    return path


def patch_view(source: str) -> str:
    if INCLUDE in source:
        return source

    section = re.search(r"@section\(\s*(['\"])content\1\s*\)", source)
    if section:
        return source[:section.end()] + "\n" + INCLUDE + source[section.end():]

    body = re.search(r"<body\b[^>]*>", source, flags=re.IGNORECASE)
    if body:
        return source[:body.end()] + "\n" + INCLUDE + source[body.end():]

    fail("Tidak menemukan @section('content') atau tag <body>; Blade tidak diubah.")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="/var/www/html/basai_tes")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    routes = root / "routes" / "web.php"
    controller = root / "app" / "Http" / "Controllers" / "Basai" / "BasaiTestController.php"

    if not routes.is_file():
        fail(f"routes/web.php tidak ditemukan: {routes}")
    if not controller.is_file():
        fail(f"BasaiTestController tidak ditemukan: {controller}")

    original_routes = routes.read_text(encoding="utf-8")
    patched_routes = original_routes
    for route_name in ROUTE_NAMES:
        patched_routes = patch_named_route(patched_routes, route_name)

    view = discover_view(controller, root)
    original_view = view.read_text(encoding="utf-8")
    patched_view = patch_view(original_view)

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = root / ".basai-backup" / f"d5h-{stamp}"
    backup.mkdir(parents=True, exist_ok=False)

    shutil.copy2(routes, backup / "web.php")
    shutil.copy2(view, backup / view.name)

    if patched_routes != original_routes:
        routes.write_text(patched_routes, encoding="utf-8")
    if patched_view != original_view:
        view.write_text(patched_view, encoding="utf-8")

    print(f"D5H_APPLIED=YES")
    print(f"BACKUP={backup}")
    print(f"VIEW={view}")
    print("ROUTES=basai.test.show,basai.test.transcribe")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"D5H_APPLIED=NO")
        print(f"ERROR={exc}", file=sys.stderr)
        raise SystemExit(1)
