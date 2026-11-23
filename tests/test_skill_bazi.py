"""各 skill 带的计算包副本与源头 lib/kanyu/ 一致；bazi-mingli 的入口、结构与出处登记。

skill 安装后是独立目录，计算包 kanyu/ 随 skill 带一份，由 tools/sync_kanyu.py 从 lib/kanyu/ 复制。
"""

import support
import filecmp
import glob
import os
import re
import subprocess
import sys
import tempfile
import unittest

SKILL = support.BAZI
ENTRY = os.path.join(SKILL, "scripts", "bazi.py")


def read(*parts):
    with open(os.path.join(*parts), encoding="utf-8") as f:
        return f.read()


class TestSync(unittest.TestCase):
    def test_kanyu_copies_are_identical(self):
        src = os.path.join(support.LIB, "kanyu")

        def files(root):
            return sorted(os.path.relpath(p, root) for p in glob.glob(os.path.join(root, "**", "*"), recursive=True)
                          if os.path.isfile(p) and "__pycache__" not in p)

        for skill in (support.FENGSHUI, support.BAZI):
            dst = os.path.join(skill, "scripts", "kanyu")
            self.assertEqual(files(src), files(dst), "运行 python3 tools/sync_kanyu.py")
            for rel in files(src):
                self.assertTrue(filecmp.cmp(os.path.join(src, rel), os.path.join(dst, rel), shallow=False),
                                f"{os.path.basename(skill)}/{rel} 与源头不一致：只改 lib/kanyu/，再运行 python3 tools/sync_kanyu.py")

    def test_glossary_md_is_generated(self):
        from kanyu import glossary
        self.assertEqual(read(SKILL, "references", "glossary.md"), glossary.markdown(),
                         "glossary.md 由 lib/kanyu/glossary.py 生成：运行 python3 tools/sync_kanyu.py")

    def test_requirements_match(self):
        for skill in (support.FENGSHUI, support.BAZI):
            self.assertEqual(read(support.ROOT, "requirements.txt"), read(skill, "requirements.txt"), skill)


class TestStructure(unittest.TestCase):
    REF = re.compile(r"`((?:references|scripts|assets)/[^`\s]+?\.(?:md|py|html|json|txt))`")

    def test_frontmatter_name(self):
        self.assertRegex(read(SKILL, "SKILL.md"), r"(?m)^name: bazi-mingli$")

    def test_skill_md_and_references(self):
        skill = read(SKILL, "SKILL.md")
        self.assertLess(len(skill.splitlines()), 500)
        refs = set(self.REF.findall(skill))
        self.assertIn("references/playbook.md", refs)
        for r in refs:
            self.assertTrue(os.path.exists(os.path.join(SKILL, r)), r)
        for p in glob.glob(os.path.join(SKILL, "references", "*.md")):
            text = read(p)
            self.assertEqual([r for r in self.REF.findall(text) if r.endswith(".md")], [], os.path.basename(p))
            self.assertEqual(re.findall(r"\]\((?!https?://)[^)]+\.md\)", text), [], os.path.basename(p))

    def test_every_book_registered(self):
        registry = read(SKILL, "references", "sources.md").replace("·", "")
        for p in [os.path.join(SKILL, "SKILL.md")] + glob.glob(os.path.join(SKILL, "references", "*.md")):
            if p.endswith("sources.md"):
                continue
            for title in set(re.findall(r"《([^》]+)》", read(p))) - {"书名"}:   # 书名：引用格式的占位符
                self.assertTrue(title.replace("·", "") in registry, f"{title}（{os.path.basename(p)}）未登记")


@support.needs_lunar
class TestEntry(unittest.TestCase):
    def test_text_and_html(self):
        with tempfile.TemporaryDirectory() as td:
            r = subprocess.run([sys.executable, ENTRY, "--birth", "1990-06-01 08:30", "--gender", "f",
                                "--longitude", "116.4", "--html"], capture_output=True, text=True, cwd=td)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("四柱：年庚午  月辛巳  日丁酉  时甲辰", r.stdout)
            page = os.path.join(td, "八字命盘-庚午辛巳丁酉甲辰.html")
            self.assertTrue(os.path.exists(page))
            self.assertIn("bazi-mingli", read(page))

    def test_errors(self):
        r = subprocess.run([sys.executable, ENTRY, "--birth", "1985", "--gender", "m"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 1)
        self.assertIn("年月日", r.stderr)
        r = subprocess.run([sys.executable, ENTRY, "-h"], capture_output=True, text=True)
        self.assertIn("--zi", r.stdout)


if __name__ == "__main__":
    unittest.main()
