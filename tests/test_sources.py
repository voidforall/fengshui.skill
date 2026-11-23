"""出处登记检查：fengshui-master 的 SKILL、参考资料与对话示例中提到的每一部典籍，都必须登记在它的 references/sources.md；
仓库首页与文档提到的典籍须登记在 fengshui-master 或 bazi-mingli 的出处表（八字 skill 自身的检查见 test_skill_bazi.py）。

新增引用时先在 sources.md 写明出处与核对状态，否则此测试失败。
"""

import support
import glob
import os
import re
import unittest

SKILL = support.FENGSHUI
FILES = [os.path.join(SKILL, "SKILL.md")] + sorted(
    glob.glob(os.path.join(SKILL, "references", "*.md"))
    + glob.glob(os.path.join(SKILL, "examples", "*.md")))
REPO_DOCS = ["README.md", "CONTRIBUTING.md", os.path.join("docs", "how-it-works.md")]

PLACEHOLDERS = {"书名"}   # SKILL.md 中说明引用格式用的占位符

# 篇章级引用（如《易傳/說卦》）与书名中的「·」写法统一后比较
def norm(t: str) -> str:
    return t.replace("·", "").replace("周易", "").replace("易传", "").strip()


def read(path):
    if not os.path.isabs(path):
        path = os.path.join(support.ROOT, path)
    with open(path, encoding="utf-8") as f:
        return f.read()


class TestSources(unittest.TestCase):
    def test_every_book_registered(self):
        registry = norm(read(os.path.join(SKILL, "references", "sources.md")))
        both = registry + norm(read(os.path.join(support.BAZI, "references", "sources.md")))
        missing = {}
        for f in REPO_DOCS:
            for title in set(re.findall(r"《([^》]+)》", read(f))):
                if title not in PLACEHOLDERS and norm(title) not in both:
                    missing.setdefault(title, []).append(os.path.basename(f))
        for f in FILES:
            if f.endswith("sources.md"):
                continue
            for title in set(re.findall(r"《([^》]+)》", read(f))):
                if title not in PLACEHOLDERS and norm(title) not in registry:
                    missing.setdefault(title, []).append(os.path.basename(f))
        self.assertEqual(missing, {}, "以下书名未登记在 references/sources.md")

    def test_status_markers_defined(self):
        s = read(os.path.join(SKILL, "references", "sources.md"))
        for mark in ("✅", "🧮", "📖", "⚖", "✂"):
            self.assertIn(mark, s)


if __name__ == "__main__":
    unittest.main()
