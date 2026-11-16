import support
import datetime as dt
import unittest


@support.needs_lunar
class TestBazi(unittest.TestCase):
    def test_pillars(self):
        from kanyu.bazi import bazi
        b = bazi(dt.datetime(1990, 6, 1, 8, 30), "f")
        self.assertEqual(b.ganzhi, ["庚午", "辛巳", "丁酉", "甲辰"])
        self.assertEqual(b.mingua.number, 8)
        self.assertEqual(sum(b.wuxing_count.values()), 8)
        self.assertEqual([p.gan_shishen for p in b.pillars], ["正财", "偏财", "日主", "正印"])
        self.assertEqual([h.gan for h in b.pillars[1].hidden], list("丙庚戊"))

    def test_true_solar_time_changes_hour(self):
        from kanyu.bazi import bazi
        # 北京时间 07:05，乌鲁木齐（87.6°E）真太阳时约 04:55 → 寅时而非辰时
        b = bazi(dt.datetime(1990, 1, 10, 7, 5), "m", longitude=87.6)
        self.assertEqual(b.ganzhi[3][1], "寅")
        self.assertLess(b.moment.solar_delta, -120)

    def test_lichun_boundary(self):
        from kanyu.bazi import bazi
        b = bazi(dt.datetime(1990, 1, 20, 12), "m")
        self.assertEqual(b.ganzhi[0], "己巳")      # 立春前仍属上一年
        self.assertEqual(b.mingua.year, 1989)


@support.needs_lunar
class TestBirthTime(unittest.TestCase):
    """出生时间口径：夏令时、子时换日、时辰不详、海外时区。"""

    def test_china_dst_is_removed(self):
        from kanyu.bazi import bazi
        # 1988 年夏令时 4/17–9/11：钟表 09:20 实为标准时 08:20 → 辰时，而非巳时
        b = bazi(dt.datetime(1988, 7, 1, 9, 20), "m")
        self.assertEqual(b.moment.dst_minutes, 60)
        self.assertEqual(b.ganzhi[3][1], "辰")
        # 夏令时以外不扣
        self.assertEqual(bazi(dt.datetime(1988, 12, 1, 9, 20), "m").moment.dst_minutes, 0)
        self.assertEqual(bazi(dt.datetime(1988, 12, 1, 9, 20), "m").ganzhi[3][1], "巳")

    def test_zi_rule(self):
        from kanyu.bazi import bazi
        nxt = bazi(dt.datetime(1990, 2, 3, 23, 30), "f")
        same = bazi(dt.datetime(1990, 2, 3, 23, 30), "f", zi="same")
        self.assertEqual(nxt.ganzhi[2:], ["庚子", "丙子"])    # 23:00 起换日
        self.assertEqual(same.ganzhi[2:], ["己亥", "丙子"])   # 晚子时日柱不换，时干按次日
        self.assertEqual(nxt.zi_alt["day"], "己亥")
        self.assertTrue(any("两派" in w for w in nxt.warnings))
        self.assertIsNone(bazi(dt.datetime(1990, 2, 3, 22, 30), "f").zi_alt)

    def test_time_unknown(self):
        from kanyu.bazi import bazi
        b = bazi(dt.datetime(1985, 12, 20), "m", time_known=False)
        self.assertEqual(len(b.pillars), 3)
        self.assertEqual(b.ganzhi, ["乙丑", "戊子", "癸巳"])
        self.assertTrue(b.dayun)
        # 当日交立春：提示年柱、月柱可能不准
        b = bazi(dt.datetime(1990, 2, 4), "f", time_known=False)
        self.assertTrue(any("立春" in w and "年柱" in w for w in b.warnings))

    def test_overseas_month_by_absolute_time(self):
        from kanyu.bazi import bazi
        # 1990 立夏为北京时间 5/6 02:35。纽约 5/5 14:00（EDT）= 北京 5/6 02:00 → 仍在立夏前，月柱庚辰
        b = bazi(dt.datetime(1990, 5, 5, 14, 0), "m", tz="America/New_York")
        self.assertEqual(b.ganzhi[1], "庚辰")
        self.assertEqual(b.moment.dst_minutes, 60)
        b = bazi(dt.datetime(1990, 5, 5, 15, 0), "m", tz="America/New_York")   # 北京 03:00，已交立夏
        self.assertEqual(b.ganzhi[1], "辛巳")
        self.assertEqual(b.ganzhi[2][1], bazi(dt.datetime(1990, 5, 5, 12), "m").ganzhi[2][1])  # 日柱按当地日期

    def test_fixed_offset_and_bad_tz(self):
        from kanyu.bazi import bazi
        self.assertEqual(bazi(dt.datetime(1990, 6, 1, 8, 30), "f", tz="UTC+8").ganzhi[3], "甲辰")
        with self.assertRaises(ValueError):
            bazi(dt.datetime(1990, 6, 1, 8, 30), "f", tz="Mars/Base")


@support.needs_lunar
class TestFacts(unittest.TestCase):
    def setUp(self):
        from kanyu.bazi import bazi
        self.b = bazi(dt.datetime(1990, 6, 1, 8, 30), "f", 116.4, focus_year=2026)

    def test_siling(self):
        s = self.b.siling
        self.assertEqual((s["jie"], s["day_n"], s["ruler"]), ("立夏", 27, "丙火"))

    def test_roots_and_tou(self):
        day = next(r for r in self.b.roots if r["pillar"] == "日")
        self.assertEqual([(x["pillar"], x["hidden"]) for x in day["roots"]], [("年", "丁"), ("月", "丙")])
        self.assertIn({"pillar": "月", "zhi": "巳", "hidden": "庚", "qi": "中气", "at": ["年"]}, self.b.tou)

    def test_relations_and_shensha(self):
        labels = [r["label"] for r in self.b.relations["zhi"]]
        self.assertIn("日支酉、时支辰 六合", labels)
        self.assertTrue(any("三合缺丑" in x for x in labels))
        names = {(x["name"], x["basis"]) for x in self.b.shensha}
        self.assertIn(("禄", "日干丁"), names)
        self.assertIn(("天乙贵人", "日干丁"), names)

    def test_timeline(self):
        b = self.b
        self.assertEqual(b.qiyun_date, dt.date(1999, 3, 1))
        self.assertEqual([d.start_age for d in b.dayun[:2]], [(8, 9), (18, 9)])
        self.assertEqual(b.focus_dayun, "戊寅")
        self.assertEqual((b.focus.ganzhi, b.focus.age), ("丙午", 36))
        self.assertIn("流年支午与年支午自刑", b.focus.relations)
        self.assertEqual([y.year for y in b.dayun[0].years], list(range(1999, 2009)))

    def test_tiaohou(self):
        t = self.b.tiaohou
        self.assertEqual(t["month"], "四月")
        self.assertTrue(t["passages"][0]["text"].startswith("四月丁火乘旺"))


class TestWuxing(unittest.TestCase):
    def test_count(self):
        from kanyu.bazi import wuxing_count, wuxing_hidden
        self.assertEqual(wuxing_count(["甲子", "丙午"]), {"木": 1, "火": 2, "土": 0, "金": 0, "水": 1})
        self.assertEqual(wuxing_hidden(["甲子", "丙午"]), {"木": 0, "火": 1, "土": 1, "金": 0, "水": 1})


if __name__ == "__main__":
    unittest.main()
