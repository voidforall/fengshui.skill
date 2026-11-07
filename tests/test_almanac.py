import support
import datetime as dt
import unittest

from kanyu import almanac as al


class TestParse(unittest.TestCase):
    def test_formats(self):
        self.assertEqual(al.parse_date("2026-05-20"), dt.datetime(2026, 5, 20))
        self.assertEqual(al.parse_date("2026-05-20 09:30"), dt.datetime(2026, 5, 20, 9, 30))
        self.assertEqual(al.parse_date("2026/05/20"), dt.datetime(2026, 5, 20))
        self.assertEqual(al.parse_date("20260520"), dt.datetime(2026, 5, 20))
        self.assertEqual(al.parse_date("1990"), dt.datetime(1990, 6, 1))
        with self.assertRaises(ValueError):
            al.parse_date("昨天")

    def test_has_time(self):
        self.assertTrue(al.has_time("2026-05-20 09:30"))
        self.assertFalse(al.has_time("2026-05-20"))


class TestRules(unittest.TestCase):
    """不依赖历法库的纯规则。"""

    def test_day_flags(self):
        self.assertEqual(al.day_flags("午", "巳", "丁亥", "破"), (["月破"], []))
        self.assertEqual(al.day_flags("午", "巳", "戊子", "危"), ([], ["岁破日"]))
        self.assertEqual(al.day_flags("午", "巳", "癸巳", "建"), ([], ["受死"]))
        self.assertEqual(al.day_flags("午", "寅", "庚申", "破"), (["月破", "正四废"], []))
        self.assertEqual(al.day_flags("午", "巳", "甲午", "成"), ([], []))

    def test_shousi_table(self):
        self.assertEqual(al.SHOUSI["寅"], "戌")
        self.assertEqual(al.SHOUSI["丑"], "酉")
        self.assertEqual(len(set(al.SHOUSI)), 12)

    def test_true_solar_time(self):
        # 东经 120° 只剩均时差（≤ 约 17 分钟）
        _, delta = al.true_solar_time(dt.datetime(2026, 6, 1, 12), 120)
        self.assertLess(abs(delta), 17)
        # 每差 1° 经度差 4 分钟
        _, d1 = al.true_solar_time(dt.datetime(2026, 6, 1, 12), 116)
        self.assertAlmostEqual(d1 - delta, -16)

    def test_lichun_approx_shape(self):
        y, _ = al.lichun_year(dt.datetime(1990, 1, 20))
        self.assertEqual(y, 1989)


@support.needs_lunar
class TestLunar(unittest.TestCase):
    def test_lichun_exact(self):
        self.assertEqual(al.lichun_year(dt.datetime(1990, 1, 20)), (1989, True))
        self.assertEqual(al.lichun_year(dt.datetime(1990, 2, 10)), (1990, True))

    def test_month_index(self):
        self.assertEqual(al.month_index(dt.datetime(2026, 5, 20)), (2026, 4))   # 巳月
        self.assertEqual(al.month_index(dt.datetime(2026, 1, 20)), (2025, 12))  # 丑月

    def test_day(self):
        i = al.day_info(dt.datetime(2026, 11, 4, 12))
        self.assertEqual((i.day_gz, i.jianchu, i.month_zhi), ("壬午", "成", "戌"))
        self.assertIn("月破", al.day_info(dt.datetime(2026, 5, 13, 12)).flags)
        self.assertIn("岁破日", al.day_info(dt.datetime(2026, 5, 14, 12)).suji)
        self.assertIn("受死", al.day_info(dt.datetime(2026, 5, 19, 12)).suji)

    def test_jianchu_po_is_chong_month(self):
        # 破日即日支冲月建
        from kanyu.core import chong
        for k in range(60):
            i = al.day_info(dt.datetime(2026, 3, 1, 12) + dt.timedelta(days=k))
            self.assertEqual(i.jianchu == "破", i.day_gz[1] == chong(i.month_zhi), i.date)


if __name__ == "__main__":
    unittest.main()
