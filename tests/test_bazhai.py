import support  # noqa: F401
import unittest

from kanyu import bazhai as b
from kanyu.core import PALACE_DIR


class TestMingua(unittest.TestCase):
    def test_known(self):
        cases = [(1985, "m", 6), (1985, "f", 9), (1990, "m", 1), (1990, "f", 8),
                 (1988, "m", 3), (1988, "f", 3), (2000, "m", 9), (2000, "f", 6),
                 (2005, "m", 4), (1986, "m", 2), (1977, "f", 1), (2009, "m", 9)]
        for y, g, n in cases:
            self.assertEqual(b.mingua(y, g), n, (y, g))

    def test_five_rule(self):
        # 男命五寄坤，女命五寄艮
        self.assertEqual((b.mingua_raw(1986, "m"), b.mingua(1986, "m")), (5, 2))
        self.assertEqual((b.mingua_raw(1990, "f"), b.mingua(1990, "f")), (5, 8))
        self.assertEqual(b.mingua_of(1986, "男").jigong, "男命五寄坤")
        self.assertEqual(b.mingua_of(1990, "女").jigong, "女命五寄艮")
        self.assertEqual(b.mingua_of(1985, "m").jigong, "")

    def test_male_female_relation(self):
        # 同年男女原始命卦数之和恒 ≡ 6 (mod 9)
        for y in range(1900, 2100):
            self.assertEqual((b.mingua_raw(y, "m") + b.mingua_raw(y, "f")) % 9, 6, y)


class TestYounian(unittest.TestCase):
    def test_kan(self):
        t = b.younian("坎")
        self.assertEqual({k: PALACE_DIR[v] for k, v in t.items()}, {
            "伏位": "北", "生气": "东南", "延年": "南", "天医": "东",
            "祸害": "西", "六煞": "西北", "五鬼": "东北", "绝命": "西南"})

    def test_qian(self):
        t = b.younian("乾")
        self.assertEqual((t["生气"], t["延年"], t["天医"], t["绝命"]), ("兑", "坤", "艮", "离"))

    def test_symmetric_and_groups(self):
        for a in b.BAZHAI_ORDER:
            ta = b.younian(a)
            self.assertEqual(sorted(ta.values()), sorted(b.BAZHAI_ORDER))
            for k, other in ta.items():
                self.assertEqual(b.younian(other)[k], a)  # 游年关系对称
                # 四吉方必在同组（东四/西四），四凶方必在异组
                same = b.east_west(a) == b.east_west(other)
                self.assertEqual(same, k in b.YOUNIAN_JI, (a, k, other))


if __name__ == "__main__":
    unittest.main()
