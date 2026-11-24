"""版本号一致性：三个 skill 的 SKILL.md、kanyu.__version__、CHANGELOG 最新条目用同一个版本号（与 Release 一致）。"""

import support
import os
import re
import unittest

import kanyu


def read(name):
    with open(os.path.join(support.ROOT, name), encoding="utf-8") as f:
        return f.read()


class TestVersion(unittest.TestCase):
    def test_consistent(self):
        root = os.path.join(support.ROOT, "skills")
        skills = sorted(n for n in os.listdir(root) if os.path.exists(os.path.join(root, n, "SKILL.md")))
        self.assertGreaterEqual(len(skills), 3)
        for name in skills:            # 每个 skill 都与仓库版本一致，新增 skill 自动纳入
            skill = re.search(r'version:\s*"([^"]+)"', read(os.path.join("skills", name, "SKILL.md"))).group(1)
            self.assertEqual(skill, kanyu.__version__, name)
        changelog = re.search(r"^## \[(\d+\.\d+\.\d+)\]", read("CHANGELOG.md"), re.M).group(1)
        self.assertEqual(changelog, kanyu.__version__)


if __name__ == "__main__":
    unittest.main()
