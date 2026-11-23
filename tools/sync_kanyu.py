"""把计算包源头 lib/kanyu/ 复制到各个需要它的 skill，并生成由它派生的参考文档。

每个 skill 安装后是独立目录，不能跨目录 import，也不能用指向目录外的符号链接（安装时会被丢掉），
所以计算包要随 skill 带一份真实文件。每个 skill 只带自己用到的模块，清单见 MANIFEST。

只改 lib/kanyu/，改完运行：python3 tools/sync_kanyu.py
tests/test_skill_bazi.py 检查：每个源头模块都在清单里、副本与源头逐字节一致、副本能单独导入、glossary.md 已更新。
"""

import os
import shutil
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
SOURCE = os.path.join(ROOT, "lib", "kanyu")

SHARED = ["__init__.py", "core.py", "almanac.py", "bazhai.py", "cli.py", "pages.py"]
MANIFEST = {
    "fengshui-master": SHARED + ["feixing.py", "zibai.py", "zeri.py",
                                 "render.py", "pages_feixing.py", "cli_fengshui.py"],
    "bazi-mingli": SHARED + ["ganzhi.py", "bazi.py", "glossary.py", "data/qiongtong.json",
                             "render_bazi.py", "pages_bazi.py", "cli_bazi.py"],
}
GLOSSARY_MD = os.path.join(ROOT, "skills", "bazi-mingli", "references", "glossary.md")


def target(skill: str) -> str:
    return os.path.join(ROOT, "skills", skill, "scripts", "kanyu")


def sync() -> list[str]:
    done = []
    for skill, files in MANIFEST.items():
        dst = target(skill)
        if os.path.exists(dst):
            shutil.rmtree(dst)
        for rel in files:
            os.makedirs(os.path.dirname(os.path.join(dst, rel)), exist_ok=True)
            shutil.copy2(os.path.join(SOURCE, rel), os.path.join(dst, rel))
        done.append(dst)
    sys.path.insert(0, os.path.join(ROOT, "lib"))
    from kanyu import glossary
    with open(GLOSSARY_MD, "w", encoding="utf-8") as f:
        f.write(glossary.markdown())
    return done + [GLOSSARY_MD]


if __name__ == "__main__":
    for t in sync():
        print("已同步", os.path.relpath(t, ROOT))
