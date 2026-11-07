"""skill 结构须符合 Agent Skills 规范（agentskills.io/specification）的建议：

- SKILL.md 正文不超过 500 行
- SKILL.md 中引用的文件都存在
- 引用只有一层：references/ 下的流程文档不再引用其他文件
（frontmatter 与命名由 CI 中的 `agentskills validate` 校验）
"""

import support
import glob
import os
import re
import unittest

ROOT = support.ROOT
REF = re.compile(r"`((?:references|scripts|assets|examples)/[^`\s]+?\.(?:md|py|html|json))`")


def read(p):
    with open(os.path.join(ROOT, p), encoding="utf-8") as f:
        return f.read()


class TestStructure(unittest.TestCase):
    def test_skill_md_length(self):
        self.assertLess(len(read("SKILL.md").splitlines()), 500)

    def test_referenced_files_exist(self):
        refs = set(REF.findall(read("SKILL.md")))
        self.assertTrue(refs)
        for r in refs:
            self.assertTrue(os.path.exists(os.path.join(ROOT, r)), r)

    def test_every_playbook_is_routed(self):
        skill = read("SKILL.md")
        for p in glob.glob(os.path.join(ROOT, "references", "playbook-*.md")):
            self.assertIn("references/" + os.path.basename(p), skill)

    def test_references_are_one_level(self):
        for p in glob.glob(os.path.join(ROOT, "references", "*.md")):
            text = read(os.path.relpath(p, ROOT))
            md_refs = [r for r in REF.findall(text) if r.endswith(".md")]
            self.assertEqual(md_refs, [], os.path.basename(p))
            self.assertEqual(re.findall(r"\]\((?!https?://)[^)]+\.md\)", text), [], os.path.basename(p))


if __name__ == "__main__":
    unittest.main()
