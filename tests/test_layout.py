"""户型对位：房间方位解析、各房间的飞星与八宅吉凶、页面数据。"""

import support  # noqa: F401
import json
import os
import tempfile
import unittest

from kanyu import cli, pages
from kanyu.feixing import feixing_chart
from kanyu.layout import make_member, parse_palace, parse_rooms, read_rooms


class TestParse(unittest.TestCase):
    def test_palace_names(self):
        self.assertEqual([parse_palace(x) for x in ("南", "正南", "西北", "离", "中", "中宫")],
                         ["离", "离", "乾", "离", "中", "中"])
        with self.assertRaises(ValueError):
            parse_palace("左边")

    def test_rooms(self):
        self.assertEqual(parse_rooms("大门=南，主卧=西北, 厨房 = 震"),
                         [("大门", "离"), ("主卧", "乾"), ("厨房", "震")])
        for bad in ("大门南", "=南", "大门=南,大门=北"):
            with self.assertRaises(ValueError, msg=bad):
                parse_rooms(bad)


class TestReadings(unittest.TestCase):
    def setUp(self):
        self.ch = feixing_chart(8, "子")       # 坎宅
        self.me = make_member("我", 1985, "m")  # 乾命
        self.rs = {r.name: r for r in read_rooms(self.ch, parse_rooms("大门=南,主卧=西北,客厅=中"), [self.me], 1)}

    def test_stars(self):
        door = self.rs["大门"]
        self.assertEqual((door.palace, door.shan, door.xiang, door.yun, door.annual), ("离", 8, 8, 3, 5))
        self.assertEqual(self.rs["主卧"].flags, ["五黄", "二五交加"])

    def test_bazhai(self):
        # 坎宅：南延年、西北六煞；乾命：南绝命、西北伏位
        self.assertEqual((self.rs["大门"].house_younian, self.rs["大门"].house_ji), ("延年", True))
        self.assertEqual((self.rs["主卧"].house_younian, self.rs["主卧"].house_ji), ("六煞", False))
        self.assertEqual(self.rs["大门"].members["我"], "绝命")
        self.assertEqual(self.rs["主卧"].members["我"], "伏位")
        self.assertIsNone(self.rs["客厅"].house_younian)   # 中宫无游年


class TestCliAndPage(unittest.TestCase):
    ARGS = ["feixing", "--facing", "180", "--yun", "8", "--annual", "2026",
            "--rooms", "大门=南,主卧=西北", "--member", "我:1985-03-01:m", "--member", "太太:1990-06-01:f"]

    def test_text_and_json(self):
        out, _ = cli.run(self.ARGS)
        self.assertIn("房间对位（宅卦：坎宅", out.text)
        self.assertIn("家人 太太：8 艮卦，西四命", out.text)
        self.assertEqual(out.data["rooms"][0]["name"], "大门")

    def test_member_format(self):
        with self.assertRaises(ValueError):
            cli.run(["feixing", "--facing", "180", "--yun", "8", "--member", "我1985m"])

    def test_page_data(self):
        with tempfile.TemporaryDirectory() as td:
            notes = os.path.join(td, "n.json")
            with open(notes, "w", encoding="utf-8") as f:
                json.dump({"rooms": {"主卧": "批注"}}, f, ensure_ascii=False)
            out, _ = cli.run(self.ARGS + ["--html", os.path.join(td, "p.html"), "--notes", notes])
            with open(out.data["html"], encoding="utf-8") as f:
                d = pages.extract_data(f.read())
        placed = {r["name"]: r["palace"] for r in d["rooms"]}
        self.assertEqual((placed["大门"], placed["主卧"]), ("离", "乾"))
        self.assertIsNone(placed["书房"])                  # 签筒里的空签
        self.assertEqual(d["house"]["gua"], "坎")
        self.assertEqual(d["house"]["younian"]["离"], "延年")
        self.assertEqual([m["gua"] for m in d["members"]], ["乾", "艮"])
        self.assertEqual(d["notes"]["rooms"]["主卧"], "批注")

    def test_notes_rooms_validation(self):
        with tempfile.TemporaryDirectory() as td:
            p = os.path.join(td, "n.json")
            with open(p, "w", encoding="utf-8") as f:
                json.dump({"rooms": ["x"]}, f)
            with self.assertRaises(ValueError):
                pages.load_notes(p)


if __name__ == "__main__":
    unittest.main()
