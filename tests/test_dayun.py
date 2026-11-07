"""大运排法对照古籍命例（第 1 层 eval，不调用模型）。

数据：tests/data/ditiansui_dayun.json —— 自《滴天髓阐微》原文抽取的命例及书中所列大运。
"""

import support
import datetime as dt
import json
import os
import unittest

from kanyu.bazi import dayun_forward, dayun_from_pillars

with open(os.path.join(os.path.dirname(__file__), "data", "ditiansui_dayun.json"), encoding="utf-8") as f:
    DATA = json.load(f)


class TestDitiansui(unittest.TestCase):
    def test_dataset_size(self):
        self.assertGreaterEqual(len(DATA["cases"]), 480)

    def test_every_case(self):
        bad = []
        for c in DATA["cases"]:
            if c["gender"] == "?":
                continue
            got = dayun_from_pillars(c["pillars"], c["gender"], len(c["dayun"]))
            if got != c["dayun"]:
                bad.append((c["id"], c["line"], c["pillars"], c["dayun"], got))
        self.assertEqual(bad, [])

    def test_unsure_cases_documented(self):
        unsure = [c for c in DATA["cases"] if c["gender"] == "?"]
        self.assertTrue(all(c.get("note") for c in unsure))
        self.assertLessEqual(len(unsure), 2)

    def test_women_chapter(self):
        women = [c for c in DATA["cases"] if c["gender"] == "f"]
        self.assertEqual(len(women), 27)


class TestRule(unittest.TestCase):
    def test_forward(self):
        self.assertTrue(dayun_forward("甲", "m"))
        self.assertFalse(dayun_forward("乙", "m"))
        self.assertFalse(dayun_forward("甲", "f"))
        self.assertTrue(dayun_forward("乙", "f"))

    def test_qianlong(self):
        # 乾隆：辛卯 丁酉 庚午 丙子，阴年男命逆排（阐微原书此例大运漏「甲午」一步，故不在数据集中）
        self.assertEqual(dayun_from_pillars(["辛卯", "丁酉", "庚午", "丙子"], "m", 4),
                         ["丙申", "乙未", "甲午", "癸巳"])


@support.needs_lunar
class TestAgainstLunar(unittest.TestCase):
    def test_matches_bazi(self):
        from kanyu.bazi import bazi
        for d, g in [(dt.datetime(1990, 6, 1, 8, 30), "f"), (dt.datetime(1985, 12, 20, 23, 30), "m"),
                     (dt.datetime(2001, 3, 3, 3, 3), "m"), (dt.datetime(1977, 9, 9, 9, 9), "f")]:
            b = bazi(d, g)
            self.assertEqual(dayun_from_pillars(b.pillars, g, 8), [x.ganzhi for x in b.dayun], (d, g))


if __name__ == "__main__":
    unittest.main()
