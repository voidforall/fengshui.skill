#!/usr/bin/env python3
"""从 CHANGELOG.md 取出某个版本的条目，作为 GitHub Release 正文。

用法：python3 .github/scripts/release_notes.py <版本号，如 2.2.0> [CHANGELOG 路径]
找不到该版本的条目时以非零状态退出，发版随之中止。
"""

import re
import sys


def notes_for(changelog: str, version: str) -> str:
    m = re.search(rf"^## \[{re.escape(version)}\][^\n]*\n(.*?)(?=^## \[|^\[[^\]]+\]: |\Z)", changelog, re.S | re.M)
    if not m:
        raise SystemExit(f"CHANGELOG 中没有 [{version}] 的条目")
    body = m.group(1).strip()
    if not body:
        raise SystemExit(f"CHANGELOG 中 [{version}] 的条目为空")
    return body + "\n"


if __name__ == "__main__":
    version = sys.argv[1]
    path = sys.argv[2] if len(sys.argv) > 2 else "CHANGELOG.md"
    with open(path, encoding="utf-8") as f:
        sys.stdout.write(notes_for(f.read(), version))
