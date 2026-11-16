"""干支查表规则（纯标准库）。出处见 references/sources.md「八、八字查表」。"""

import support  # noqa: F401
import unittest

from kanyu import ganzhi as g
from kanyu.core import GAN, JIAZI, ZHI


class TestShishen(unittest.TestCase):
    def test_jia(self):
        self.assertEqual([g.shishen("甲", x) for x in GAN],
                         ["比肩", "劫财", "食神", "伤官", "偏财", "正财", "七杀", "正官", "偏印", "正印"])

    def test_yin_day(self):
        self.assertEqual(g.shishen("丁", "庚"), "正财")
        self.assertEqual(g.shishen("丁", "癸"), "七杀")


class TestChangsheng(unittest.TestCase):
    def test_sheng_and_si_from_sanming(self):
        # 《三命通会》「论天干阴阳生死」：甲生亥死午，乙生午死亥，丙戊生寅死酉，丁己生酉死寅，
        # 庚生巳死子，辛生子死巳，壬生申死卯，癸生卯死申
        for gan, sheng, si in [("甲", "亥", "午"), ("乙", "午", "亥"), ("丙", "寅", "酉"), ("戊", "寅", "酉"),
                               ("丁", "酉", "寅"), ("己", "酉", "寅"), ("庚", "巳", "子"), ("辛", "子", "巳"),
                               ("壬", "申", "卯"), ("癸", "卯", "申")]:
            self.assertEqual(g.changsheng(gan, sheng), "长生", gan)
            self.assertEqual(g.changsheng(gan, si), "死", gan)

    def test_linguan_is_lu(self):
        for gan in GAN:
            self.assertEqual(g.changsheng(gan, g.LU[gan]), "临官", gan)


class TestSiling(unittest.TestCase):
    def test_every_month_sums_to_30(self):
        for z in ZHI:
            self.assertEqual(sum(d for _, d in g.SILING[z]), 30, z)

    def test_lookup(self):
        self.assertEqual(g.siling("寅", 5), "艮土")
        self.assertEqual(g.siling("寅", 6), "丙火")
        self.assertEqual(g.siling("寅", 11), "甲木")
        self.assertEqual(g.siling("寅", 31), "甲木")


class TestRelations(unittest.TestCase):
    def test_pairs(self):
        self.assertEqual(g.pair_relations("子", "午"), ["冲"])
        self.assertEqual(g.pair_relations("子", "丑"), ["六合"])
        self.assertEqual(g.pair_relations("寅", "巳"), ["刑", "害"])
        self.assertEqual(g.pair_relations("午", "午"), ["自刑"])
        self.assertEqual(g.pair_relations("子", "子"), [])
        self.assertEqual(g.pair_relations("甲", "己"), ["合"])

    def test_sanhe_needs_all_three(self):
        full = g.relations([("年支", "申"), ("月支", "子"), ("日支", "辰"), ("时支", "午")])
        self.assertTrue(any(r["kind"] == "三合" and r["wuxing"] == "水" for r in full))
        part = g.relations([("年支", "申"), ("月支", "子"), ("日支", "午")])
        self.assertFalse(any(r["kind"] == "三合" for r in part))
        self.assertTrue(any(r["kind"] == "三合缺一" and r["missing"] == "辰" for r in part))

    def test_against_natal(self):
        rel = g.against_natal("丙午", ["庚午", "辛巳", "丁酉", "甲辰"], "流年")
        self.assertEqual(rel, ["流年干丙合月干辛", "流年支午与年支午自刑"])
        rel = g.against_natal("丁未", ["庚午", "辛巳", "丁酉", "甲辰"], "大运")
        self.assertIn("大运支未与月支巳、年支午三会火方", rel)


class TestXunkongShensha(unittest.TestCase):
    def test_xunkong(self):
        self.assertEqual(g.xunkong("甲子"), "戌亥")
        self.assertEqual(g.xunkong("癸酉"), "戌亥")
        self.assertEqual(g.xunkong("甲戌"), "申酉")
        self.assertEqual(g.xunkong("癸亥"), "子丑")
        self.assertEqual(len({g.xunkong(x) for x in JIAZI}), 6)

    def test_shensha(self):
        hits = {(x["name"], x["basis"]): x["hits"] for x in g.shensha(["庚午", "辛巳", "丁酉", "甲辰"])}
        self.assertEqual(hits[("禄", "日干丁")], ["年支午"])
        self.assertEqual(hits[("空亡", "日柱丁酉旬")], ["月支巳", "时支辰"])
        # 申子辰马在寅、咸池在酉
        hits = {(x["name"], x["basis"]): x["hits"] for x in g.shensha(["甲子", "丙寅", "戊申", "辛酉"])}
        self.assertEqual(hits[("驿马", "年支子")], ["月支寅"])
        self.assertEqual(hits[("咸池（桃花）", "日支申")], ["时支酉"])
        self.assertNotIn(("羊刃", "日干戊"), hits)


if __name__ == "__main__":
    unittest.main()
