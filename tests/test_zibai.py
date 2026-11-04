import support
import unittest

from kanyu import zibai as z


class TestZibai(unittest.TestCase):
    def test_annual_center(self):
        known = {2017: 1, 2020: 7, 2022: 5, 2023: 4, 2024: 3, 2025: 2, 2026: 1, 2027: 9}
        for y, c in known.items():
            self.assertEqual(z.annual_center(y), c, y)

    def test_monthly(self):
        self.assertEqual(z.monthly_center(2026, 1), 8)   # 午年寅月八白
        self.assertEqual(z.monthly_center(2024, 1), 5)   # 辰年寅月五黄
        self.assertEqual(z.monthly_center(2025, 1), 2)   # 巳年寅月二黑
        self.assertEqual(z.monthly_center(2026, 9), 9)

    def test_year_sha(self):
        s = z.year_sha(2026)
        self.assertEqual((s.ganzhi, s.center, s.wuhuang, s.erhei), ("丙午", 1, "南", "西北"))
        self.assertTrue(s.sansha.startswith("北"))
        self.assertTrue(s.suipo.startswith("北"))
        self.assertTrue(z.year_sha(2024).sansha.startswith("南"))
        self.assertTrue(z.year_sha(2025).sansha.startswith("东"))


@support.needs_lunar
class TestAgainstLunar(unittest.TestCase):
    """与 lunar-python 独立计算交叉验证。"""

    NUM = "一二三四五六七八九"

    def test_annual(self):
        from lunar_python import Solar
        for y in range(1990, 2040):
            ns = Solar.fromYmd(y, 6, 1).getLunar().getYearNineStar()
            self.assertEqual(self.NUM.index(ns.getNumber()) + 1, z.annual_center(y), y)

    def test_monthly(self):
        import datetime as dt
        from lunar_python import Solar
        from kanyu.almanac import month_index
        for y in (2024, 2025, 2026):
            for m in range(1, 13):
                ly, mi = month_index(dt.datetime(y, m, 20))
                ns = Solar.fromYmd(y, m, 20).getLunar().getMonthNineStar()
                self.assertEqual(self.NUM.index(ns.getNumber()) + 1, z.monthly_center(ly, mi), (y, m))


if __name__ == "__main__":
    unittest.main()
