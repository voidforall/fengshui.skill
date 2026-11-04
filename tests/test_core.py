import support  # noqa: F401
import unittest

from kanyu import core as c


class TestMountains(unittest.TestCase):
    def test_deg_to_mountain(self):
        for deg, m in [(0, "子"), (352.5, "子"), (352.4, "壬"), (7.6, "癸"), (180, "午"),
                       (45, "艮"), (315, "乾"), (360, "子"), (-15, "壬")]:
            self.assertEqual(c.deg_to_mountain(deg)[0], m, deg)
        self.assertAlmostEqual(c.deg_to_mountain(187)[1], 7.0)
        self.assertAlmostEqual(c.deg_to_mountain(353)[1], -7.0)

    def test_mountain_center_roundtrip(self):
        for m in c.MOUNTAINS:
            self.assertEqual(c.deg_to_mountain(c.mountain_center_deg(m)), (m, 0.0))

    def test_xuankong_yinyang(self):
        # 坎宫：壬阳 子阴 癸阴；艮宫：丑阴 艮阳 寅阳（不同于八字地支阴阳）
        self.assertEqual([c.mountain_yinyang(m) for m in "壬子癸"], ["+", "-", "-"])
        self.assertEqual([c.mountain_yinyang(m) for m in "丑艮寅"], ["-", "+", "+"])
        self.assertEqual([c.mountain_yinyang(m) for m in "辰巽巳"], ["-", "+", "+"])
        self.assertEqual([c.mountain_yinyang(m) for m in "庚酉辛"], ["+", "-", "-"])
        self.assertEqual(sum(c.mountain_yinyang(m) == "+" for m in c.MOUNTAINS), 12)

    def test_opposite_and_palace(self):
        self.assertEqual(c.opposite("子"), "午")
        self.assertEqual(c.opposite("艮"), "坤")
        self.assertEqual(c.opposite("亥"), "巳")
        for m in c.MOUNTAINS:
            self.assertEqual(c.mountain_yuanlong(m), c.mountain_yuanlong(c.opposite(m)))
            self.assertEqual(c.palace_mountain(c.mountain_palace(m), c.mountain_yuanlong(m)), m)

    def test_parse_direction(self):
        self.assertEqual(c.parse_direction("午"), ("午", None))
        self.assertEqual(c.parse_direction("187°"), ("午", 187.0))
        self.assertEqual(c.parse_direction("187.5"), ("丁", 187.5))   # 交界归下一山
        self.assertEqual(c.parse_direction(" 90度"), ("卯", 90.0))
        with self.assertRaises(ValueError):
            c.parse_direction("南")


class TestFly(unittest.TestCase):
    def test_luoshu(self):
        # 五入中顺飞即洛书本位
        self.assertEqual(c.fly(5), c.PALACE_NUM)

    def test_backward(self):
        self.assertEqual(c.fly(5, False)["乾"], 4)
        self.assertEqual(c.fly(1, False)["乾"], 9)


class TestYears(unittest.TestCase):
    def test_ganzhi(self):
        self.assertEqual(c.ganzhi_of_year(1984), "甲子")
        self.assertEqual(c.ganzhi_of_year(2026), "丙午")

    def test_yun(self):
        for y, yun in [(1864, 1), (1984, 7), (2023, 8), (2024, 9), (2043, 9), (2044, 1)]:
            self.assertEqual(c.yun_of_year(y), yun, y)
        self.assertEqual(c.yun_range(9), (2024, 2043))

    def test_gender(self):
        self.assertEqual(c.parse_gender("男"), "m")
        self.assertEqual(c.parse_gender("F"), "f")
        with self.assertRaises(ValueError):
            c.parse_gender("x")


if __name__ == "__main__":
    unittest.main()
