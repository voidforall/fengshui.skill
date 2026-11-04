"""确定性计算的回归测试。运行：python3 -m unittest discover -s tests

测试用例取自公认的结论（游年歌诀、各运旺山旺向表、紫白年星等），
用于保证计算不出错；派别有争议之处不在测试范围内。
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import fengshui as f  # noqa: E402


class TestMountains(unittest.TestCase):
    def test_deg_to_mountain(self):
        self.assertEqual(f.deg_to_mountain(0)[0], "子")
        self.assertEqual(f.deg_to_mountain(352.5)[0], "子")
        self.assertEqual(f.deg_to_mountain(352.4)[0], "壬")
        self.assertEqual(f.deg_to_mountain(7.6)[0], "癸")
        self.assertEqual(f.deg_to_mountain(180)[0], "午")
        self.assertEqual(f.deg_to_mountain(45)[0], "艮")
        self.assertEqual(f.deg_to_mountain(315)[0], "乾")
        self.assertAlmostEqual(f.deg_to_mountain(187)[1], 7.0)

    def test_xuankong_yinyang(self):
        # 坎宫：壬阳 子阴 癸阴；艮宫：丑阴 艮阳 寅阳（不同于八字地支阴阳）
        self.assertEqual([f.mountain_yinyang(m) for m in "壬子癸"], ["+", "-", "-"])
        self.assertEqual([f.mountain_yinyang(m) for m in "丑艮寅"], ["-", "+", "+"])
        self.assertEqual([f.mountain_yinyang(m) for m in "辰巽巳"], ["-", "+", "+"])
        self.assertEqual([f.mountain_yinyang(m) for m in "庚酉辛"], ["+", "-", "-"])
        self.assertEqual(sum(f.mountain_yinyang(m) == "+" for m in f.MOUNTAINS), 12)

    def test_opposite(self):
        self.assertEqual(f.opposite("子"), "午")
        self.assertEqual(f.opposite("艮"), "坤")
        self.assertEqual(f.opposite("亥"), "巳")


class TestMingua(unittest.TestCase):
    def test_known(self):
        cases = [(1985, "m", 6), (1985, "f", 9), (1990, "m", 1), (1990, "f", 8),
                 (1988, "m", 3), (1988, "f", 3), (2000, "m", 9), (2000, "f", 6),
                 (2005, "m", 4), (1986, "m", 2), (1977, "f", 1), (2009, "m", 9)]
        for y, g, n in cases:
            self.assertEqual(f.mingua(y, g), n, (y, g))

    def test_five_rule(self):
        # 男命五寄坤，女命五寄艮
        self.assertEqual(f.mingua(1986, "m"), 2)   # 原始数为 5
        self.assertEqual(f.mingua_raw(1986, "m"), 5)
        self.assertEqual(f.mingua(1990, "f"), 8)
        self.assertEqual(f.mingua_raw(1990, "f"), 5)

    def test_male_female_relation(self):
        # 同年男女原始命卦数之和恒 ≡ 6 (mod 9)
        for y in range(1900, 2100):
            self.assertEqual((f.mingua_raw(y, "m") + f.mingua_raw(y, "f")) % 9, 6, y)


class TestBazhai(unittest.TestCase):
    def test_kan(self):
        t = f.younian("坎")
        self.assertEqual({k: f.PALACE_DIR[v] for k, v in t.items()}, {
            "伏位": "北", "生气": "东南", "延年": "南", "天医": "东",
            "祸害": "西", "六煞": "西北", "五鬼": "东北", "绝命": "西南"})

    def test_qian(self):
        t = f.younian("乾")
        self.assertEqual((t["生气"], t["延年"], t["天医"], t["绝命"]), ("兑", "坤", "艮", "离"))

    def test_symmetric_and_groups(self):
        for a in f.BAZHAI_ORDER:
            ta = f.younian(a)
            self.assertEqual(sorted(ta.values()), sorted(f.BAZHAI_ORDER))
            for k, b in ta.items():
                self.assertEqual(f.younian(b)[k], a)  # 游年关系对称
                # 四吉方必在同组（东四/西四），四凶方必在异组
                same = f.east_west(a) == f.east_west(b)
                self.assertEqual(same, k in f.YOUNIAN_JI, (a, k, b))


class TestFeixing(unittest.TestCase):
    def pattern(self, yun, sit):
        p = f.feixing_chart(yun, sit)["patterns"]
        return p[0].split("（")[0] if p and "当令" in p[0] else None

    def test_8yun_zi_wu_grid(self):
        ch = f.feixing_chart(8, "子")
        self.assertEqual([ch["yunpan"][p] for p in "巽离坤震中兑艮坎乾"], [7, 3, 5, 6, 8, 1, 2, 4, 9])
        self.assertEqual([ch["shan"][p] for p in "巽离坤震中兑艮坎乾"], [3, 8, 1, 2, 4, 6, 7, 9, 5])
        self.assertEqual([ch["xiang"][p] for p in "巽离坤震中兑艮坎乾"], [4, 8, 6, 5, 3, 1, 9, 7, 2])
        self.assertEqual(self.pattern(8, "子"), "双星到向")

    def test_wangshan_wangxiang(self):
        exp = {7: set("卯乙辰酉辛戌"), 8: set("丑巽巳未乾亥")}
        for yun, sits in exp.items():
            got = {m for m in f.MOUNTAINS if self.pattern(yun, m) == "旺山旺向"}
            self.assertEqual(got, sits, yun)

    def test_shangshan_xiashui(self):
        exp = {7: set("甲巽巳庚乾亥"), 8: set("艮寅辰坤申戌")}
        for yun, sits in exp.items():
            got = {m for m in f.MOUNTAINS if self.pattern(yun, m) == "上山下水"}
            self.assertEqual(got, sits, yun)

    def test_9yun_all_shuangxing(self):
        # 九运下卦二十四山皆为双星到向/到坐，无旺山旺向、上山下水
        for m in f.MOUNTAINS:
            self.assertIn(self.pattern(9, m), ("双星到向", "双星到坐"), m)

    def test_8yun_genkun_fuyin(self):
        pats = f.feixing_chart(8, "艮")["patterns"]
        self.assertTrue(any("伏吟" in p for p in pats))

    def test_tigua_mechanics(self):
        ch = f.feixing_chart(8, "子", tigua=True)
        # 山星 4 入中，依巽（+）顺飞，巽替星为 6；向星 3 依卯（-）逆飞，卯替星为 2
        self.assertEqual(ch["shan"]["中"], 6)
        self.assertEqual(ch["xiang"]["中"], 2)
        self.assertTrue(ch["shan_info"][2])
        self.assertFalse(ch["xiang_info"][2])


class TestYearly(unittest.TestCase):
    def test_yun(self):
        self.assertEqual(f.yun_of_year(2023), 8)
        self.assertEqual(f.yun_of_year(2024), 9)
        self.assertEqual(f.yun_of_year(2043), 9)
        self.assertEqual(f.yun_of_year(2044), 1)
        self.assertEqual(f.yun_of_year(1984), 7)

    def test_annual_center(self):
        known = {2017: 1, 2020: 7, 2022: 5, 2023: 4, 2024: 3, 2025: 2, 2026: 1, 2027: 9}
        for y, c in known.items():
            self.assertEqual(f.annual_center(y), c, y)

    def test_year_sha(self):
        s = f.year_sha(2026)
        self.assertEqual(s["ganzhi"], "丙午")
        self.assertTrue(s["sansha"].startswith("北"))
        self.assertTrue(s["suipo"].startswith("北"))
        self.assertEqual(s["wuhuang"], "南")

    def test_monthly(self):
        self.assertEqual(f.monthly_center(2026, 1), 8)   # 午年寅月八白
        self.assertEqual(f.monthly_center(2024, 1), 5)   # 辰年寅月五黄
        self.assertEqual(f.monthly_center(2025, 1), 2)   # 巳年寅月二黑
        self.assertEqual(f.monthly_center(2026, 9), 9)


@unittest.skipUnless(f.HAS_LUNAR, "需要 lunar_python")
class TestCalendar(unittest.TestCase):
    def test_annual_matches_lunar(self):
        for y in range(1990, 2040):
            ns = f.Solar.fromYmd(y, 6, 1).getLunar().getYearNineStar()
            self.assertEqual("一二三四五六七八九".index(ns.getNumber()) + 1, f.annual_center(y), y)

    def test_monthly_matches_lunar(self):
        import datetime as dt
        for y in (2024, 2025, 2026):
            for m in range(1, 13):
                d = dt.datetime(y, m, 20)
                ly, mi = f._month_index(d)
                ns = f.Solar.fromYmd(y, m, 20).getLunar().getMonthNineStar()
                self.assertEqual("一二三四五六七八九".index(ns.getNumber()) + 1, f.monthly_center(ly, mi), (y, m))

    def test_lichun(self):
        import datetime as dt
        self.assertEqual(f.lichun_year(dt.datetime(1990, 1, 20)), (1989, True))
        self.assertEqual(f.lichun_year(dt.datetime(1990, 2, 10)), (1990, True))

    def test_day(self):
        import datetime as dt
        i = f.day_info(dt.datetime(2026, 11, 4, 12))
        self.assertEqual((i["day_gz"], i["jianchu"]), ("壬午", "成"))
        self.assertIn("月破", f.day_info(dt.datetime(2026, 5, 13, 12))["flags"])
        self.assertIn("岁破", f.day_info(dt.datetime(2026, 5, 14, 12))["flags"])
        self.assertIn("受死", f.day_info(dt.datetime(2026, 5, 19, 12))["flags"])


if __name__ == "__main__":
    unittest.main()
