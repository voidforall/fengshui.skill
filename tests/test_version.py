"""版本号一致性：SKILL.md、kanyu.__version__、CHANGELOG 最新条目。"""

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
        skill = re.search(r'version:\s*"([^"]+)"', read("SKILL.md")).group(1)
        changelog = re.search(r"^## \[(\d+\.\d+\.\d+)\]", read("CHANGELOG.md"), re.M).group(1)
        self.assertEqual(skill, kanyu.__version__)
        self.assertEqual(changelog, kanyu.__version__)


if __name__ == "__main__":
    unittest.main()
