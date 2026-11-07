"""自动发版用的 CHANGELOG 条目提取（.github/scripts/release_notes.py）。"""

import support
import importlib.util
import os
import unittest

spec = importlib.util.spec_from_file_location(
    "release_notes", os.path.join(support.ROOT, ".github", "scripts", "release_notes.py"))
rn = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rn)

with open(os.path.join(support.ROOT, "CHANGELOG.md"), encoding="utf-8") as f:
    CHANGELOG = f.read()


class TestReleaseNotes(unittest.TestCase):
    def test_current_version_has_notes(self):
        import kanyu
        body = rn.notes_for(CHANGELOG, kanyu.__version__)
        self.assertGreater(len(body), 50)
        self.assertNotIn("## [", body)

    def test_last_entry_stops_before_link_definitions(self):
        body = rn.notes_for(CHANGELOG, "1.0.0")
        self.assertNotIn("]: https://", body)

    def test_missing_version(self):
        with self.assertRaises(SystemExit):
            rn.notes_for(CHANGELOG, "9.9.9")

    def test_no_unreleased_on_release(self):
        # 发版提交中不应残留 Unreleased（否则其内容不会进入任何 Release）
        import kanyu
        top = CHANGELOG.split("\n## [", 2)[1]
        self.assertTrue(top.startswith(kanyu.__version__) or top.startswith("Unreleased"))


if __name__ == "__main__":
    unittest.main()
