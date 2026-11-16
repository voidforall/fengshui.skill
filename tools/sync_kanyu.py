"""把根目录 scripts/kanyu/（唯一源头）复制到各个需要它的子 skill。

每个 skill 安装后是独立目录，不能跨目录 import，所以计算包要随 skill 带一份。
只改 scripts/kanyu/，改完运行：python3 tools/sync_kanyu.py
tests/test_skill_bazi.py 检查副本与源头逐字节一致。
"""

import os
import shutil
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
SOURCE = os.path.join(ROOT, "scripts", "kanyu")
TARGETS = [os.path.join(ROOT, "skills", "bazi-mingli", "scripts", "kanyu")]
IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc")


def sync() -> list[str]:
    for dst in TARGETS:
        if os.path.exists(dst):
            shutil.rmtree(dst)
        shutil.copytree(SOURCE, dst, ignore=IGNORE)
    return TARGETS


if __name__ == "__main__":
    for t in sync():
        print("已同步", os.path.relpath(t, ROOT))
    sys.exit(0)
