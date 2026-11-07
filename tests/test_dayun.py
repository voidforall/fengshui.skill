"""大运排法（阳男阴女顺、阴男阳女逆，自月柱起）。

例子取自《滴天髓阐微》，书中所列大运与此一致。曾对该书 485 个命例做过一次性全量核对，全部一致；
需要复现时用 evals/tools/extract_ditiansui.py 抽取命例。
"""

import support
import datetime as dt
import unittest

from kanyu.bazi import dayun_forward, dayun_from_pillars


class TestDayun(unittest.TestCase):
    def test_rule(self):
        self.assertTrue(dayun_forward("甲", "m"))
        self.assertFalse(dayun_forward("乙", "m"))
        self.assertFalse(dayun_forward("甲", "f"))
        self.assertTrue(dayun_forward("乙", "f"))

    def test_ditiansui_examples(self):
        cases = [
            # 阳年男命顺排：董中堂造（通神论·知命）
            (["庚申", "庚辰", "戊辰", "戊午"], "m", ["辛巳", "壬午", "癸未", "甲申", "乙酉", "丙戌", "丁亥", "戊子"]),
            # 阴年男命逆排（通神论·理气）
            (["丁亥", "庚戌", "甲辰", "壬申"], "m", ["己酉", "戊申", "丁未", "丙午", "乙巳", "甲辰"]),
            # 阴年女命顺排（六亲论·女命章）
            (["丁未", "乙巳", "甲午", "丁卯"], "f", ["丙午", "丁未", "戊申", "己酉", "庚戌", "辛亥"]),
        ]
        for pillars, g, book in cases:
            self.assertEqual(dayun_from_pillars(pillars, g, len(book)), book, pillars)

    def test_qianlong(self):
        # 乾隆：辛卯 丁酉 庚午 丙子，阴年男命逆排（阐微原书此例大运漏「甲午」一步）
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
