import support  # noqa: F401
import unittest

from kanyu import feixing as fx
from kanyu.core import MOUNTAINS

ORDER = "巽离坤震中兑艮坎乾"   # 九宫格阅读顺序（上南下北）


class TestChart(unittest.TestCase):
    def test_8yun_zi_wu_grid(self):
        ch = fx.feixing_chart(8, "子")
        self.assertEqual([ch.yunpan[p] for p in ORDER], [7, 3, 5, 6, 8, 1, 2, 4, 9])
        self.assertEqual([ch.shan[p] for p in ORDER], [3, 8, 1, 2, 4, 6, 7, 9, 5])
        self.assertEqual([ch.xiang[p] for p in ORDER], [4, 8, 6, 5, 3, 1, 9, 7, 2])
        self.assertEqual(fx.main_pattern(ch), "双星到向")
        self.assertEqual((ch.shan_entry.by, ch.shan_entry.forward), ("巽", True))
        self.assertEqual((ch.xiang_entry.by, ch.xiang_entry.forward), ("卯", False))

    def test_five_uses_own_mountain(self):
        ch = fx.feixing_chart(9, "子")   # 九运坎宫运星为 5
        self.assertEqual((ch.shan_entry.n, ch.shan_entry.by), (5, "子"))


class TestPatterns(unittest.TestCase):
    def pattern(self, yun, sit):
        return fx.main_pattern(fx.feixing_chart(yun, sit))

    def test_wangshan_wangxiang(self):
        exp = {7: set("卯乙辰酉辛戌"), 8: set("丑巽巳未乾亥")}
        for yun, sits in exp.items():
            got = {m for m in MOUNTAINS if self.pattern(yun, m) == "旺山旺向"}
            self.assertEqual(got, sits, yun)

    def test_shangshan_xiashui(self):
        exp = {7: set("甲巽巳庚乾亥"), 8: set("艮寅辰坤申戌")}
        for yun, sits in exp.items():
            got = {m for m in MOUNTAINS if self.pattern(yun, m) == "上山下水"}
            self.assertEqual(got, sits, yun)

    def test_9yun_all_shuangxing(self):
        # 九运下卦二十四山皆为双星到向/到坐，无旺山旺向、上山下水
        for m in MOUNTAINS:
            self.assertIn(self.pattern(9, m), ("双星到向", "双星到坐"), m)

    def test_reverse_mountain_swaps_pattern(self):
        swap = {"旺山旺向": "旺山旺向", "上山下水": "上山下水",
                "双星到向": "双星到坐", "双星到坐": "双星到向", None: None}
        from kanyu.core import opposite
        for yun in range(1, 10):
            for m in MOUNTAINS:
                self.assertEqual(self.pattern(yun, opposite(m)), swap[self.pattern(yun, m)], (yun, m))

    def test_8yun_genkun_fuyin(self):
        pats = fx.feixing_chart(8, "艮").patterns
        self.assertTrue(any("伏吟" in p for p in pats))


class TestTigua(unittest.TestCase):
    def test_table_complete(self):
        self.assertEqual(set(fx.TIGUA_STAR), set(MOUNTAINS))

    def test_mechanics(self):
        ch = fx.feixing_chart(8, "子", tigua=True)
        # 山星 4 入中，依巽（+）顺飞，巽替星为 6；向星 3 依卯（-）逆飞，卯替星为 2
        self.assertEqual((ch.shan["中"], ch.shan_entry.forward, ch.shan_entry.replaced), (6, True, True))
        self.assertEqual((ch.xiang["中"], ch.xiang_entry.forward), (2, False))

    def test_five_not_replaced(self):
        ch = fx.feixing_chart(9, "子", tigua=True)
        self.assertEqual(ch.shan["中"], 5)
        self.assertFalse(ch.shan_entry.replaced)


class TestHelpers(unittest.TestCase):
    def test_star_status_9yun(self):
        got = {n: fx.star_status(n, 9) for n in range(1, 10)}
        self.assertEqual(got[9], "当令旺星")
        self.assertEqual(got[1], "生气（下运旺）")
        self.assertEqual(got[2], "次生气")
        self.assertEqual(got[8], "退气")
        self.assertEqual(got[7], "衰气")
        self.assertEqual(got[5], "五黄煞")

    def test_palace_flags(self):
        self.assertEqual(fx.palace_flags(5, 2), ["五黄", "二五交加"])
        self.assertEqual(fx.palace_flags(1, 2, 5), ["五黄", "二五交加"])
        self.assertEqual(fx.palace_flags(1, 3, 4), [])

    def test_jian_warnings(self):
        self.assertEqual(fx.jian_warnings("子", 2.0), [])
        self.assertEqual(len(fx.jian_warnings("子", 4.0)), 1)
        w = fx.jian_warnings("子", 7.0)
        self.assertIn("小空亡", w[0])       # 子/癸 同宫
        self.assertIn("大空亡", fx.jian_warnings("癸", 7.0)[0])   # 癸/丑 出卦


if __name__ == "__main__":
    unittest.main()
