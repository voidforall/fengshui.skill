"""只给四柱（--pillars）：不依赖历法库；查表事实与按出生时间排盘的结果一致。"""

import support  # noqa: F401
import datetime as dt
import unittest

from kanyu import cli
from kanyu.bazi import chart_from_pillars, parse_pillars
from kanyu.ganzhi import climate, root_weight


class TestPillarsChart(unittest.TestCase):
    def test_parse(self):
        self.assertEqual(parse_pillars("庚申 庚辰 戊辰 戊午"), ["庚申", "庚辰", "戊辰", "戊午"])
        self.assertEqual(parse_pillars("庚申庚辰戊辰戊午"), ["庚申", "庚辰", "戊辰", "戊午"])
        self.assertEqual(parse_pillars("庚申，庚辰，戊辰"), ["庚申", "庚辰", "戊辰"])
        for bad in ("庚申 庚辰", "甲丑 庚辰 戊辰 戊午", "庚申 庚辰 戊辰 戊午 甲子"):
            with self.assertRaises(ValueError, msg=bad):
                parse_pillars(bad)

    def test_root_weight_follows_ditiansui(self):
        # 《滴天髓阐微》「衰旺」：长生禄旺为重根；墓库余气为轻根（如甲乙逢未、辰，丙丁逢戌，庚辛逢丑，壬癸逢辰）
        for gan, zhi in (("甲", "亥"), ("甲", "寅"), ("壬", "申"), ("丙", "巳"), ("戊", "辰")):
            self.assertEqual(root_weight(gan, zhi), "重根", gan + zhi)
        for gan, zhi in (("甲", "未"), ("乙", "辰"), ("丙", "戌"), ("庚", "丑"), ("壬", "辰")):
            self.assertEqual(root_weight(gan, zhi), "轻根", gan + zhi)

    def test_climate_facts(self):
        c = climate(["庚申", "庚辰", "戊辰", "戊午"])
        self.assertEqual(c["season"], "春月")
        self.assertEqual(c["fire"], ["时支午本气丁"])
        self.assertEqual(c["wet_earth"], ["月支辰", "日支辰"])
        self.assertEqual(c["dry_earth"], [])
        self.assertEqual(climate(["丁亥", "壬子", "庚子", "辛巳"])["season"], "冬月，寒")

    def test_dayun_and_facts(self):
        c = chart_from_pillars(["庚申", "庚辰", "戊辰", "戊午"], "m")
        self.assertEqual([d["ganzhi"] for d in c.dayun[:3]], ["辛巳", "壬午", "癸未"])   # 阳年男顺排
        self.assertEqual(c.tiaohou["month_zhi"], "辰")
        self.assertTrue(all("weight" in x for r in c.roots for x in r["roots"]))

    @support.needs_lunar
    def test_same_facts_as_birth_chart(self):
        from kanyu.bazi import bazi
        b = bazi(dt.datetime(1990, 6, 1, 8, 30), "f", 116.4, focus_year=2026)
        c = chart_from_pillars(b.ganzhi, "f")
        self.assertEqual([p.nayin for p in c.pillars], [p.nayin for p in b.pillars])
        self.assertEqual([(p.gan_shishen, p.changsheng, p.xunkong) for p in c.pillars],
                         [(p.gan_shishen, p.changsheng, p.xunkong) for p in b.pillars])
        self.assertEqual(c.relations, b.relations)
        self.assertEqual(c.shensha, b.shensha)
        self.assertEqual(c.tiaohou, b.tiaohou)
        self.assertEqual(c.wangxiang, b.wangxiang)
        self.assertEqual([d["ganzhi"] for d in c.dayun], [d.ganzhi for d in b.dayun[:8]])

    def test_cli(self):
        out, _ = cli.run(["bazi", "--pillars", "庚申 庚辰 戊辰 戊午", "--gender", "m"])
        self.assertIn("寒暖燥湿", out.text)
        self.assertIn("重根", out.text)
        self.assertIn("三春戊土", out.text)                    # 调候原文
        for bad in (["bazi", "--gender", "m"],
                    ["bazi", "--pillars", "庚申 庚辰 戊辰 戊午", "--gender", "m", "--birth", "1990-01-01"],
                    ["bazi", "--pillars", "庚申 庚辰", "--gender", "m"]):
            with self.assertRaises(cli.UsageError, msg=bad):
                cli.run(bad)


if __name__ == "__main__":
    unittest.main()
