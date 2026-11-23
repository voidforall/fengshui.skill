"""英文术语表：脚本会输出的每个术语都有英文名；生成的 terms-en.md 已更新；各 skill 分流到英文作答约定。"""

import support
import os
import re
import unittest

from kanyu import glossary, terms_en
from kanyu.bazhai import YOUNIAN_ORDER
from kanyu.core import GAN, PALACE_NUM, STAR_NAMES, ZHI
from kanyu.feixing import palace_flags, star_status
from kanyu.zeri import EVENTS


def zh_terms(*lists):
    return {zh for lst in lists for zh, _, _ in lst}


class TestCoverage(unittest.TestCase):
    def test_stems_branches_palaces_elements(self):
        self.assertEqual(set(terms_en.GAN), set(GAN))
        self.assertEqual(set(terms_en.ZHI), set(ZHI))
        self.assertEqual(set(terms_en.PALACES), set(PALACE_NUM))
        self.assertEqual(set(terms_en.ELEMENTS), set("木火土金水"))

    def test_fengshui_terms(self):
        self.assertEqual(set(terms_en.STARS), set(STAR_NAMES))
        self.assertEqual(set(terms_en.YOUNIAN), set(YOUNIAN_ORDER))
        self.assertEqual(set(terms_en.JIANCHU), set("建除满平定执破危成收开闭"))
        self.assertEqual(set(terms_en.EVENTS), set(EVENTS))
        names = zh_terms(terms_en.COMMON, terms_en.FENGSHUI)
        statuses = {star_status(n, yun).split("（")[0] for n in range(1, 10) for yun in range(1, 10)}
        self.assertEqual(statuses - names, set())
        flags = {f for s in range(1, 10) for x in range(1, 10) for f in palace_flags(s, x, 2)}
        self.assertEqual(flags - names, set())
        # 格局名：feixing.py 中输出的每个格局都要有英文
        with open(os.path.join(support.LIB, "kanyu", "feixing.py"), encoding="utf-8") as f:
            src = f.read()
        patterns = {"旺山旺向", "上山下水", "双星到向", "双星到坐", "伏吟", "反吟", "合十", "父母三般卦", "连珠三般卦"}
        for p in patterns:
            self.assertIn(p, src)
        self.assertEqual(patterns - names, set())

    def test_bazi_terms(self):
        self.assertEqual(set(terms_en.SHISHEN), set(glossary.SHISHEN))
        self.assertEqual(set(terms_en.CHANGSHENG), set(glossary.CHANGSHENG))
        self.assertEqual(set(terms_en.WANGXIANG), set(glossary.WANGXIANG))
        names = zh_terms(terms_en.COMMON, terms_en.BAZI)
        self.assertEqual(set(glossary.TERMS) - names, set(), "glossary.TERMS 的每个术语都要有英文名")

    def test_no_conflicting_duplicates_within_a_domain(self):
        for lst in (terms_en.COMMON + terms_en.FENGSHUI, terms_en.COMMON + terms_en.BAZI):
            seen = {}
            for zh, en, _ in lst:
                self.assertEqual(seen.setdefault(zh, en), en, zh)

    def test_life_stages_have_plain_english(self):
        for zh, (en, plain) in terms_en.CHANGSHENG.items():
            self.assertTrue(plain and "death" not in plain.lower(), zh)


class TestSkills(unittest.TestCase):
    def read(self, *parts):
        with open(os.path.join(*parts), encoding="utf-8") as f:
            return f.read()

    def test_generated_tables_are_current(self):
        for skill, domain in (("fengshui-master", "fengshui"), ("bazi-mingli", "bazi")):
            self.assertEqual(self.read(support.SKILLS, skill, "references", "terms-en.md"), terms_en.markdown(domain),
                             f"{skill}：运行 python3 tools/sync_kanyu.py")

    def test_skills_route_english_users(self):
        triggers = {"fengshui-master": "feng shui", "bazi-mingli": "bazi", "city-wuxing-map": "Five Elements"}
        for skill, word in triggers.items():
            text = self.read(support.SKILLS, skill, "SKILL.md")
            description = re.search(r"description: \|\n(.*?)\nlicense:", text, re.S).group(1)
            self.assertIn(word, description.lower() if word.islower() else description, skill)
            self.assertLessEqual(len(re.sub(r"\s+", " ", description)), 1024, skill)
            self.assertIn("`references/english.md`", text, skill)
            self.assertTrue(os.path.exists(os.path.join(support.SKILLS, skill, "references", "english.md")), skill)


if __name__ == "__main__":
    unittest.main()
