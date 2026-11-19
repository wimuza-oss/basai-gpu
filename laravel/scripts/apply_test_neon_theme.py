#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime
from pathlib import Path
import shutil
import sys

ROOT = Path("/var/www/html/basai_tes")
VIEW = ROOT / "resources/views" / "basai" / "test-audio.blade.php"

PHP_BLOCK = """@php
    $neonBase = file_exists(public_path('neon/assets/css/neon-core.css'))
        ? asset('neon/assets')
        : asset('public/neon/assets');
@endphp

"""

ASSETS = """
    <link rel="icon" href="{{ $neonBase }}/images/favicon.ico">
    <link rel="stylesheet" href="{{ $neonBase }}/js/jquery-ui/css/no-theme/jquery-ui-1.10.3.custom.min.css">
    <link rel="stylesheet" href="{{ $neonBase }}/css/font-icons/entypo/css/entypo.css">
    <link rel="stylesheet" href="{{ $neonBase }}/css/font-icons/font-awesome/css/font-awesome.min.css">
    <link rel="stylesheet" href="{{ $neonBase }}/css/bootstrap.css">
    <link rel="stylesheet" href="{{ $neonBase }}/css/neon-core.css">
    <link rel="stylesheet" href="{{ $neonBase }}/css/neon-theme.css">
    <link rel="stylesheet" href="{{ $neonBase }}/css/neon-forms.css">
    <link rel="stylesheet" href="{{ $neonBase }}/css/custom.css">
"""

OVERRIDES = r"""
    <style id="basai-test-neon-theme">
        body.basai-test-page {
            max-width: none;
            margin: 0;
            padding: 0;
            background: #f5f5f6;
            color: #303641;
            font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
        }

        .basai-test-shell {
            max-width: 1180px;
            margin: 0 auto;
            padding: 28px 24px 48px;
        }

        .basai-test-heading {
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 20px;
            margin-bottom: 22px;
        }

        .basai-test-heading h1 {
            margin: 0 0 6px;
            font-size: 27px;
            font-weight: 300;
            color: #303641;
        }

        .basai-test-heading .subtitle {
            margin: 0;
            color: #949494;
            font-size: 13px;
        }

        .basai-test-badge {
            display: inline-block;
            padding: 5px 9px;
            border-radius: 3px;
            background: #21a9e1;
            color: #fff;
            font-size: 11px;
            font-weight: 600;
            white-space: nowrap;
        }

        .basai-userbar {
            margin: 0 0 22px !important;
            padding: 12px 15px !important;
            border: 1px solid #ebebeb !important;
            border-radius: 3px !important;
            background: #fff !important;
            box-shadow: none !important;
        }

        .basai-userbar__logout {
            border: 1px solid #d9d9d9 !important;
            border-radius: 3px !important;
            padding: 7px 12px !important;
            background: #fff !important;
            color: #303641 !important;
        }

        .basai-test-page fieldset {
            margin: 0 0 18px;
            padding: 20px;
            border: 1px solid #ebebeb;
            border-radius: 3px;
            background: #fff;
            box-shadow: none;
        }

        .basai-test-page legend {
            width: auto;
            margin: 0 0 12px;
            padding: 0 8px 0 0;
            border: 0;
            color: #373e4a;
            font-size: 15px;
            font-weight: 600;
        }

        .basai-test-page button {
            border: 1px solid #d8d8d8;
            border-radius: 3px;
            padding: 8px 14px;
            background: #fff;
            color: #373e4a;
            transition: background .15s ease, border-color .15s ease;
        }

        .basai-test-page button:hover:not(:disabled) {
            background: #f3f3f3;
            border-color: #c7c7c7;
        }

        .basai-test-page button[type="submit"],
        .basai-test-page #start-record {
            border-color: #21a9e1;
            background: #21a9e1;
            color: #fff;
        }

        .basai-test-page button[type="submit"]:hover:not(:disabled),
        .basai-test-page #start-record:hover:not(:disabled) {
            border-color: #1595c8;
            background: #1595c8;
        }

        .basai-test-page input[type="file"],
        .basai-test-page input[type="number"],
        .basai-test-page select {
            border: 1px solid #ebebeb;
            border-radius: 3px;
            padding: 8px 10px;
            background: #fff;
        }

        .basai-test-page audio {
            width: 100%;
            margin-top: 12px;
        }

        .basai-test-page pre {
            border: 1px solid #ebebeb;
            border-radius: 3px;
            background: #fafafa;
            color: #303641;
        }

        .basai-test-page .error {
            border: 1px solid #f2c4c4;
            border-radius: 3px;
            background: #fff2f2;
            color: #a94442;
        }

        .basai-test-page .success {
            border: 1px solid #c9e6c9;
            border-radius: 3px;
            background: #f2fbf2;
            color: #3c763d;
        }

        .basai-test-page .muted {
            color: #949494;
        }

        @media (max-width: 768px) {
            .basai-test-shell {
                padding: 18px 12px 36px;
            }

            .basai-test-heading {
                display: block;
            }

            .basai-test-badge {
                margin-top: 10px;
            }
        }
    </style>
"""

HEAD_OLD = "    <title>BAS-AI Test Audio</title>"
HEAD_NEW = HEAD_OLD + ASSETS

BODY_OLD = "<body>"
BODY_NEW = """<body class="page-body basai-test-page">
<div class="basai-test-shell">"""

TITLE_OLD = "<h1>BAS-AI — Test Audio</h1>"
TITLE_NEW = """<div class="basai-test-heading">
    <div>
        <h1>BAS-AI — Test Audio</h1>
        <p class="subtitle">Pengujian teknis rekam / upload audio dan pipeline GPU STT</p>
    </div>
    <span class="basai-test-badge">MESIN TEKNIS</span>
</div>"""

SCRIPT_MARKER = "\\n<script>"
SCRIPT_REPLACEMENT = "\\n</div>\\n\\n<script>"

def replace_once(source: str, old: str, new: str, label: str) -> str:
    if new in source:
        return source
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected 1 marker, found {count}")
    return source.replace(old, new, 1)

def main() -> int:
    if not VIEW.is_file():
        raise RuntimeError(f"View tidak ditemukan: {VIEW}")

    source = VIEW.read_text(encoding="utf-8")

    if "basai-test-neon-theme" in source:
        print("THEME_ALREADY_APPLIED=YES")
        return 0

    updated = source
    if not updated.startswith("@php"):
        updated = PHP_BLOCK + updated

    updated = replace_once(updated, HEAD_OLD, HEAD_NEW, "title")
    updated = replace_once(updated, "</head>", OVERRIDES + "\\n</head>", "head")
    updated = replace_once(updated, BODY_OLD, BODY_NEW, "body")
    updated = replace_once(updated, TITLE_OLD, TITLE_NEW, "heading")
    updated = replace_once(updated, SCRIPT_MARKER, SCRIPT_REPLACEMENT, "script")

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = ROOT / ".basai-backup" / f"test-neon-{stamp}"
    backup.mkdir(parents=True, exist_ok=False)
    shutil.copy2(VIEW, backup / VIEW.name)

    VIEW.write_text(updated, encoding="utf-8")

    print("THEME_APPLIED=YES")
    print(f"BACKUP={backup}")
    print(f"VIEW={VIEW}")
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print("THEME_APPLIED=NO")
        print(f"ERROR={exc}", file=sys.stderr)
        raise SystemExit(1)
