import support
import datetime as dt
import unittest

from kanyu import zeri as z
from kanyu.almanac import DayInfo


def make_day(**kw) -> DayInfo:
    base = dict(date=dt.datetime(2026, 5, 20, 12), lunar="二〇二六年四月初四", year_gz="丙午",
                month_gz="癸巳", day_gz="甲午", time_gz="庚午", jieqi="立夏", month_zhi="巳",
                jianchu="平", tianshen="", huangdao=False, chong="", chong_zhi="子")
    base.update(kw)
    return DayInfo(**base)


class TestScore(unittest.TestCase):
    """规则层：用构造的 DayInfo 测打分与排除，不依赖历法库。"""

    ev = z.EVENTS["入宅"]

    def test_full_score(self):
        ds = z.score_day(make_day(yi=["入宅"], jianchu="成", huangdao=True, jishen=["天德"]), self.ev, [])
        self.assertEqual(ds.score, z.SCORE_YI + z.SCORE_BEST + z.SCORE_HUANGDAO + 2)
        self.assertEqual(ds.excluded, [])

    def test_minor_deshen(self):
        ds = z.score_day(make_day(jishen=["母仓"]), self.ev, [])
        self.assertEqual(ds.score, 1)

    def test_secondary_jianchu(self):
        self.assertEqual(z.score_day(make_day(jianchu="满"), self.ev, []).score, z.SCORE_OK)

    def test_exclusions(self):
        p = z.Person(1984, "子")
        ds = z.score_day(make_day(flags=["月破"], ji=["移徙"], yi=["入宅"]), self.ev, [p])
        self.assertEqual(ds.excluded, ["月破", "冲1984年生人（子鼠）", "黄历忌移徙"])

    def test_unknown_event(self):
        with self.assertRaises(ValueError):
            z.get_event("拜拜")


@support.needs_lunar
class TestSelect(unittest.TestCase):
    def test_may_2026(self):
        r = z.select(dt.date(2026, 5, 10), dt.date(2026, 5, 31), "入宅", [1988])
        self.assertEqual(r.good[0].info.date.date(), dt.date(2026, 5, 20))
        scores = [d.score for d in r.good]
        self.assertEqual(scores, sorted(scores, reverse=True))
        bad = {d.info.date.date(): d.excluded for d in r.bad}
        self.assertIn("月破", bad[dt.date(2026, 5, 13)])
        notes = {d.info.date.date(): d.notes for d in r.good + r.bad}
        self.assertIn("通书俗忌：岁破日", notes[dt.date(2026, 5, 14)])   # 俗忌只标注，不排除
        self.assertTrue(any("冲1988" in x for x in bad[dt.date(2026, 5, 12)]))
        self.assertEqual(len(r.good) + len(r.bad) <= 22, True)
        for d in r.good:
            self.assertGreaterEqual(d.score, z.MIN_SCORE)
            self.assertEqual(d.excluded, [])

    def test_range_limit(self):
        with self.assertRaises(ValueError):
            z.select(dt.date(2026, 1, 1), dt.date(2027, 6, 1), "入宅", [])


if __name__ == "__main__":
    unittest.main()
