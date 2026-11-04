import support
import datetime as dt
import unittest


@support.needs_lunar
class TestBazi(unittest.TestCase):
    def test_pillars(self):
        from kanyu.bazi import bazi
        b = bazi(dt.datetime(1990, 6, 1, 8, 30), "f")
        self.assertEqual(b.pillars, ["庚午", "辛巳", "丁酉", "甲辰"])
        self.assertEqual(b.mingua.number, 8)
        self.assertEqual(sum(b.wuxing_count.values()), 8)

    def test_true_solar_time_changes_hour(self):
        from kanyu.bazi import bazi
        # 北京时间 07:05，乌鲁木齐（87.6°E）真太阳时约 04:55 → 寅时而非辰时
        b = bazi(dt.datetime(1990, 6, 1, 7, 5), "m", longitude=87.6)
        self.assertEqual(b.pillars[3][1], "寅")
        self.assertLess(b.solar_delta, -120)

    def test_lichun_boundary(self):
        from kanyu.bazi import bazi
        b = bazi(dt.datetime(1990, 1, 20, 12), "m")
        self.assertEqual(b.pillars[0], "己巳")      # 立春前仍属上一年
        self.assertEqual(b.mingua.year, 1989)


class TestWuxing(unittest.TestCase):
    def test_count(self):
        from kanyu.bazi import wuxing_count
        self.assertEqual(wuxing_count(["甲子", "丙午"]), {"木": 1, "火": 2, "土": 0, "金": 0, "水": 1})


if __name__ == "__main__":
    unittest.main()
