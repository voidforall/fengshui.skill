"""出处登记检查：SKILL 与参考资料中提到的每一部典籍，都必须登记在 references/sources.md。

新增引用时先在 sources.md 写明出处与核对状态，否则此测试失败。
"""

import support
import glob
import os
import re
import unittest

FILES = ["SKILL.md", "README.md"] + sorted(
    glob.glob(os.path.join(support.ROOT, "references", "*.md"))
    + glob.glob(os.path.join(support.ROOT, "examples", "*.md")))

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
        registry = norm(read("references/sources.md"))
        missing = {}
        for f in FILES:
            if f.endswith("sources.md"):
                continue
            for title in set(re.findall(r"《([^》]+)》", read(f))):
                if title not in PLACEHOLDERS and norm(title) not in registry:
                    missing.setdefault(title, []).append(os.path.basename(f))
        self.assertEqual(missing, {}, "以下书名未登记在 references/sources.md")

    def test_status_markers_defined(self):
        s = read("references/sources.md")
        for mark in ("✅", "🧮", "📖", "⚖", "✂"):
            self.assertIn(mark, s)


if __name__ == "__main__":
    unittest.main()
