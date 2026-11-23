"""把计算包源头 lib/kanyu/ 复制到各个需要它的 skill，并生成由它派生的参考文档。

每个 skill 安装后是独立目录，不能跨目录 import，所以计算包要随 skill 带一份。
只改 lib/kanyu/，改完运行：python3 tools/sync_kanyu.py
tests/test_skill_bazi.py 检查副本与源头逐字节一致、glossary.md 与 kanyu/glossary.py 一致。
"""

import os
import shutil
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
SOURCE = os.path.join(ROOT, "lib", "kanyu")
BAZI = os.path.join(ROOT, "skills", "bazi-mingli")
TARGETS = [os.path.join(ROOT, "skills", name, "scripts", "kanyu") for name in ("fengshui-master", "bazi-mingli")]
GLOSSARY_MD = os.path.join(BAZI, "references", "glossary.md")
IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc")


def sync() -> list[str]:
    for dst in TARGETS:
        if os.path.exists(dst):
            shutil.rmtree(dst)
        shutil.copytree(SOURCE, dst, ignore=IGNORE)
    sys.path.insert(0, os.path.join(ROOT, "lib"))
    from kanyu import glossary
    with open(GLOSSARY_MD, "w", encoding="utf-8") as f:
        f.write(glossary.markdown())
    return TARGETS + [GLOSSARY_MD]


if __name__ == "__main__":
    for t in sync():
        print("已同步", os.path.relpath(t, ROOT))
    sys.exit(0)
