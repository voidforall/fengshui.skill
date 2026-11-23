"""交互盘面：数据与排盘一致、批注安全嵌入、CLI 生成文件。"""

import support  # noqa: F401
import json
import os
import tempfile
import unittest

from kanyu import cli, pages, pages_bazi, pages_feixing
from kanyu.feixing import feixing_chart

NOTES = {"summary": "总断 </script><b>不应被当作标签</b>",
         "palaces": {"离": "向首批注", "坎": "坐山批注"}, "advice": ["建议一"]}


def page_for(ch, notes=None, **kw):
    data = pages_feixing.feixing_data(ch, annual=kw.get("annual"), annual_label=None, month=None,
                              facing_deg=kw.get("deg"), yun_note="", current_yun=9, notes=notes or {})
    return pages.render("feixing.html", "飞星盘", data)


class TestFeixingPage(unittest.TestCase):
    def test_layers_match_chart(self):
        ch = feixing_chart(8, "子")
        d = pages.extract_data(page_for(ch, annual=1))
        self.assertEqual(d["layers"]["shan"], ch.shan)
        self.assertEqual(d["layers"]["xiang"], ch.xiang)
        self.assertEqual(d["layers"]["yun"], ch.yunpan)
        self.assertEqual(d["layers"]["annual"]["中"], 1)
        self.assertEqual(d["main_pattern"], "双星到向")
        self.assertEqual(d["title"], "八运 · 子山午向")
        self.assertEqual(d["chart_status"]["8"], "当令旺星")    # 八运盘，当前九运：两种旺衰都给出
        self.assertEqual(d["status"]["9"], "当令旺星")

    def test_notes_embedded_safely(self):
        html = page_for(feixing_chart(8, "子"), NOTES)
        self.assertNotIn("</script><b>", html)               # 批注里的 </script> 不会截断脚本
        self.assertEqual(pages.extract_data(html)["notes"], NOTES)

    def test_self_contained(self):
        html = page_for(feixing_chart(9, "午"))
        self.assertNotIn("<script src", html)                 # 无外部脚本；仅可选的网络字体
        self.assertIn("<title>飞星盘</title>", html)
        self.assertNotIn("__DATA__", html)

    def test_jian_warning_without_cli_flag(self):
        ch = feixing_chart(9, "坤")
        d = pages.extract_data(page_for(ch, deg=52.0))
        self.assertTrue(any("空亡" in w for w in d["warnings"]))
        self.assertFalse(any("--tigua" in w for w in d["warnings"]))

    def test_load_notes_validation(self):
        with tempfile.TemporaryDirectory() as td:
            def write(obj):
                p = os.path.join(td, "n.json")
                with open(p, "w", encoding="utf-8") as f:
                    json.dump(obj, f, ensure_ascii=False)
                return p
            self.assertEqual(pages_feixing.load_notes(write(NOTES)), NOTES)
            for bad in ({"palace": {}}, {"palaces": {"南": "x"}}, {"advice": [1]}, ["x"]):
                with self.assertRaises(ValueError, msg=bad):
                    pages_feixing.load_notes(write(bad))


class TestFeixingPageEnglish(unittest.TestCase):
    """英文页面：数据文字都译成英文，汉字只留在原文引文里；排盘数据与中文页相同。"""

    def data(self, ch, **kw):
        return pages_feixing.feixing_data(ch, annual=kw.get("annual"), annual_label="2026", month=kw.get("month"),
                                          facing_deg=kw.get("deg"), yun_note="", current_yun=9, notes={}, lang="en")

    def test_every_pattern_has_english(self):
        from kanyu.core import MOUNTAINS
        from kanyu.feixing import chart_patterns
        seen = set()
        for yun in range(1, 10):
            for m in MOUNTAINS:
                for tigua in (False, True):
                    seen.update(chart_patterns(feixing_chart(yun, m, tigua=tigua)))
        self.assertEqual(seen - set(pages_feixing.PATTERN_EN), set())

    def test_mountain_codes(self):
        self.assertEqual(pages_feixing.mountain_code("壬"), "N1")
        self.assertEqual(pages_feixing.mountain_code("子"), "N2")
        self.assertEqual(pages_feixing.mountain_code("丑"), "NE1")
        self.assertEqual(pages_feixing.mountain_code("亥"), "NW3")

    def test_english_text_has_no_chinese(self):
        import re
        ch = feixing_chart(8, "子")
        d = self.data(ch, annual=1, month=5, deg=186.5)
        zh = pages.extract_data(page_for(ch, annual=1))
        for k in ("yun", "shan", "xiang", "annual"):
            self.assertEqual(d["layers"][k], zh["layers"][k])
        visible = [d["title"], d["source"], *d["patterns"], *d["entries"], *d["warnings"],
                   *(f"{k}{v}" for k, v in d["facts"]), *d["star_names"].values(), *d["status_text"].values(),
                   *d["status_short"].values(), *(m["label"] for m in d["mountains"]),
                   *(g["label"] for g in d["gua_ring"])]
        for p in d["palaces"].values():
            visible += [p["label"], p["name"], *p["flags"], p["xiang"].split(" — ")[-1]]
        han = re.compile(r"[\u4e00-\u9fff]")
        self.assertEqual([t for t in visible if han.search(t)], [])
        self.assertEqual(d["title"], "Period 8 · Sitting Zi, Facing Wu")
        self.assertTrue(d["warnings"])

    def test_html_lang(self):
        html = pages.render("feixing.html", "Flying Star Chart", self.data(feixing_chart(9, "午")), lang="en")
        self.assertIn('<html lang="en">', html)
        self.assertIn('<html lang="zh-Hans">', page_for(feixing_chart(9, "午")))


class TestCli(unittest.TestCase):
    def test_html_default_name(self):
        with tempfile.TemporaryDirectory() as td:
            cwd = os.getcwd()
            os.chdir(td)
            try:
                out, _ = cli.run(["feixing", "--facing", "180", "--yun", "8", "--html"])
            finally:
                os.chdir(cwd)
            path = out.data["html"]
            self.assertTrue(path.endswith("飞星盘-8运-子山午向.html"))
            self.assertTrue(os.path.exists(path))
            self.assertIn("交互盘面已生成", out.text)

    def test_notes_requires_html(self):
        with self.assertRaises(cli.UsageError):
            cli.run(["feixing", "--facing", "180", "--yun", "8", "--notes", "x.json"])
        with self.assertRaises(cli.UsageError):
            cli.run(["feixing", "--facing", "180", "--yun", "8", "--lang", "en"])

    def test_english_page(self):
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "en.html")
            cli.run(["feixing", "--facing", "180", "--year", "2018-09-01", "--annual", "2026",
                     "--lang", "en", "--html", path])
            with open(path, encoding="utf-8") as f:
                d = pages.extract_data(f.read())
        self.assertEqual(d["lang"], "en")
        self.assertIn(["Annual", "2026 · star 1 at the center"], d["facts"])

    def test_example_page_is_current(self):
        # docs/examples 中的示例页面须与当前模板一致（修改模板后重新生成）
        root = support.ROOT
        with open(os.path.join(root, "docs", "examples", "feixing-demo.html"), encoding="utf-8") as f:
            demo = f.read()
        with open(os.path.join(support.FENGSHUI, "assets", "templates", "feixing.html"), encoding="utf-8") as f:
            tpl = f.read()
        head = tpl.split("__DATA__")[0].replace("__TITLE__", "飞星盘 子山午向").replace("__LANG__", "zh-Hans")
        self.assertTrue(demo.startswith(head), "示例页面已过期：重新运行 docs/examples/README 中的命令")
        with open(os.path.join(root, "docs", "examples", "feixing-demo.en.html"), encoding="utf-8") as f:
            demo_en = f.read()
        head_en = tpl.split("__DATA__")[0].replace("__TITLE__", "Flying Star Chart · Sitting Zi, Facing Wu") \
            .replace("__LANG__", "en")
        self.assertTrue(demo_en.startswith(head_en), "英文示例页面已过期：重新运行 docs/examples/README 中的命令")


BAZI_NOTES = {"plain": "白话总结", "summary": "总断 </script><b>x</b>", "basis": "依《穷通宝鉴》", "pillars": {"日": "日柱批注"},
              "dayun": {"戊寅": "大运批注"}, "years": {"2026": "流年批注"}, "advice": ["建议"]}


BAZI_SKILL = support.BAZI


@support.needs_lunar
class TestBaziPage(unittest.TestCase):
    """命盘模板随 bazi-mingli skill 发布（模板目录由 tests/support.py 登记）。"""

    def setUp(self):
        import datetime as dt
        from kanyu.bazi import bazi
        self.b = bazi(dt.datetime(1990, 6, 1, 8, 30), "f", 116.4, focus_year=2026)

    def page(self, notes=None, b=None):
        b = b or self.b
        return pages.render("bazi.html", pages_bazi.bazi_title(b), pages_bazi.bazi_data(b, notes=notes or {}))

    def test_data_matches_chart(self):
        d = pages.extract_data(self.page())
        self.assertEqual([p["gz"] for p in d["pillars"]], self.b.ganzhi)
        self.assertEqual([x["gz"] for x in d["dayun"]], [x.ganzhi for x in self.b.dayun])
        self.assertEqual(d["focus_year"], 2026)
        self.assertEqual(d["pre_years"][0]["year"], 1990)        # 起运前流年 1990–1998
        self.assertEqual(d["pre_years"][-1]["year"], 1998)
        rel = {r["label"]: r for r in d["relations"]["zhi"]}
        self.assertEqual(rel["日支酉、时支辰 六合"]["at"], [2, 3])
        self.assertEqual(rel["日支酉、时支辰 六合"]["short"], "六合")
        self.assertEqual(d["tiaohou"]["passages"], self.b.tiaohou["passages"])

    def test_plain_language_data(self):
        d = pages.extract_data(self.page())
        self.assertEqual(d["wangxiang"]["day"], "旺")              # 丁火生于巳月（夏），火旺
        g = d["glossary"]
        for p in d["pillars"]:                                      # 页面上出现的十神、长生都有白话
            self.assertTrue(p["gan_ss"] == "日主" or p["gan_ss"] in g["shishen"])
            self.assertIn(p["changsheng"], g["changsheng"])
            for x in p["hidden"]:
                self.assertIn(x["ss"], g["shishen"])
        for x in d["shensha"]:
            self.assertIn(x["name"].replace("（桃花）", ""), g["terms"])
        for k in ("合", "冲", "刑", "害", "三合", "三会", "三合缺一", "大运", "调候", "司令", "五行个数", "纳音", "空亡"):
            self.assertIn(k, g["terms"])
        self.assertEqual(g["gan_xiang"]["丁"], "在天为列星，在地为灯火")

    def test_time_unknown_three_columns(self):
        import datetime as dt
        from kanyu.bazi import bazi
        b = bazi(dt.datetime(1985, 12, 20), "m", time_known=False)
        d = pages.extract_data(self.page(b=b))
        self.assertEqual(len(d["pillars"]), 3)
        self.assertFalse(d["time_known"])

    def test_notes_embedded_safely(self):
        html = self.page(BAZI_NOTES)
        self.assertNotIn("</script><b>", html)
        self.assertEqual(pages.extract_data(html)["notes"], BAZI_NOTES)
        self.assertNotIn("<script src", html)
        self.assertNotIn("__DATA__", html)

    def test_load_bazi_notes_validation(self):
        with tempfile.TemporaryDirectory() as td:
            def write(obj):
                p = os.path.join(td, "n.json")
                with open(p, "w", encoding="utf-8") as f:
                    json.dump(obj, f, ensure_ascii=False)
                return p
            self.assertEqual(pages_bazi.load_bazi_notes(write(BAZI_NOTES)), BAZI_NOTES)
            for bad in ({"palaces": {}}, {"plain": 1}, {"pillars": {"子": "x"}}, {"years": {"明年": "x"}},
                        {"dayun": {"甲": "x"}}, {"advice": [1]}, {"summary": 1}, ["x"]):
                with self.assertRaises(ValueError, msg=bad):
                    pages_bazi.load_bazi_notes(write(bad))

    def test_cli_html(self):
        with tempfile.TemporaryDirectory() as td:
            cwd = os.getcwd()
            os.chdir(td)
            try:
                out, _ = cli.run(["bazi", "--birth", "1990-06-01 08:30", "--gender", "f", "--html"])
            finally:
                os.chdir(cwd)
            self.assertTrue(out.data["html"].endswith("八字命盘-庚午辛巳丁酉甲辰.html"))
            self.assertTrue(os.path.exists(out.data["html"]))
            self.assertIn("交互命盘已生成", out.text)
        with self.assertRaises(cli.UsageError):
            cli.run(["bazi", "--birth", "1990-06-01 08:30", "--gender", "f", "--notes", "x.json"])

    def test_example_page_is_current(self):
        root = support.ROOT
        with open(os.path.join(root, "docs", "examples", "bazi-demo.html"), encoding="utf-8") as f:
            demo = f.read()
        with open(os.path.join(BAZI_SKILL, "assets", "templates", "bazi.html"), encoding="utf-8") as f:
            tpl = f.read()
        head = tpl.split("__DATA__")[0].replace("__TITLE__", "坤造 庚午 辛巳 丁酉 甲辰").replace("__LANG__", "zh-Hans")
        self.assertTrue(demo.startswith(head), "示例页面已过期：重新运行 docs/examples/README 中的命令")
        with open(os.path.join(root, "docs", "examples", "bazi-notes.json"), encoding="utf-8") as f:
            self.assertEqual(pages.extract_data(demo)["notes"], json.load(f))
        with open(os.path.join(root, "docs", "examples", "bazi-demo.en.html"), encoding="utf-8") as f:
            demo_en = f.read()
        head_en = tpl.split("__DATA__")[0].replace("__TITLE__", "Bazi Chart · Female · Gengwu Xinsi Dingyou Jiachen") \
            .replace("__LANG__", "en")
        self.assertTrue(demo_en.startswith(head_en), "英文示例页面已过期：重新运行 docs/examples/README 中的命令")
        with open(os.path.join(root, "docs", "examples", "bazi-notes.en.json"), encoding="utf-8") as f:
            self.assertEqual(pages.extract_data(demo_en)["notes"], json.load(f))


HAN = __import__("re").compile(r"[\u4e00-\u9fff]")


@support.needs_lunar
class TestBaziPageEnglish(unittest.TestCase):
    """英文命盘：排盘数据与中文页相同，显示文字都是英文（汉字只出现在原文引文与干支字形里）。"""

    def chart(self, *args, **kw):
        import datetime as dt
        from kanyu.bazi import bazi
        return bazi(dt.datetime(*args), **kw)

    def data(self, b):
        return pages_bazi.bazi_data(b, notes={}, lang="en")

    def assertEnglish(self, texts):
        # 允许按英文约定写成「拼音 汉字」的书名，如 San Ming Tong Hui 三命通会
        allowed = __import__("re").compile(r"(San Ming Tong Hui 三命通会|Qiong Tong Bao Jian 穷通宝鉴|Yuan Hai Zi Ping 渊海子平)")
        self.assertEqual([t for t in texts if HAN.search(allowed.sub("", t))], [])

    def visible(self, d):
        out = [d["title"], d["gender"], d["source"], *d["warnings"], *d["time_lines"],
               *(f"{k}{v}" for k, v in d["facts"])]
        for kind in ("gan", "zhi"):
            out += [x for r in d["relations"][kind] for x in (r["label"], r["short"])]
        for dy in d["dayun"]:
            out += [dy["age"], dy["age_short"], *dy["relations"]]
            out += [r for y in dy["years"] for r in y["relations"]]
        out += [r for y in d["pre_years"] for r in y["relations"]]
        for x in d["shensha"]:
            out += [x["label"], x["basis"], x["targets"], *x["hits"]]
        sl = d["siling"]
        out += [sl["jie_en"], sl["ruler_en"], *(t["name_en"] for t in sl["table"]), d["wangxiang"]["season_en"]]
        out += list(d["names"].values())
        g = d["glossary"]
        out += [t for v in g["shishen"].values() for t in v] + [t for k, v in g["terms"].items() for t in v]
        out += list(g["wangxiang"].values()) + list(g["gan_xiang_en"].values())
        out += [v[0] for v in g["changsheng"].values()] + [v[2] for v in g["changsheng"].values()]
        return out

    def test_same_chart_english_text(self):
        b = self.chart(1990, 6, 1, 8, 30, gender="f", longitude=116.4, focus_year=2026)
        zh, en = pages_bazi.bazi_data(b, notes={}), self.data(b)
        self.assertEqual(en["lang"], "en")
        self.assertEqual([p["gz"] for p in en["pillars"]], [p["gz"] for p in zh["pillars"]])
        self.assertEqual([r["at"] for r in en["relations"]["zhi"]], [r["at"] for r in zh["relations"]["zhi"]])
        self.assertEqual([len(x["relations"]) for x in en["dayun"]], [len(x["relations"]) for x in zh["dayun"]])
        self.assertEnglish(self.visible(en))
        self.assertEqual(en["title"], "Bazi Chart · Female · Gengwu Xinsi Dingyou Jiachen")
        self.assertIn(("Lunar date", "year 1990, month 5, day 9"), en["facts"])
        self.assertEqual(en["relations"]["zhi"][0]["label"], "Day branch You and Hour branch Chen: Six Harmonies")
        self.assertEqual(en["names"]["旺相:死"], "Dead")             # 与十二长生的「死」分开
        self.assertEqual(en["names"]["死"], "Death")

    def test_every_warning_has_english(self):
        cases = [dict(args=(1995, 2, 4, 23, 40), kw=dict(gender="m")),                       # 子时换日
                 dict(args=(1990, 6, 6), kw=dict(gender="m", time_known=False, longitude=116.4)),  # 时辰不详、交节日
                 dict(args=(1991, 4, 14, 2, 30), kw=dict(gender="f"))]                          # 夏令时切换中不存在的时刻
        seen = 0
        for c in cases:
            b = self.chart(*c["args"], **c["kw"])
            d = self.data(b)
            self.assertEqual(len(d["warnings"]), len(b.warnings))
            self.assertEnglish(self.visible(d))
            seen += len(b.warnings)
        self.assertGreaterEqual(seen, 5)
        with self.assertRaises(ValueError):
            pages_bazi._warning_en("未知提示")

    def test_lunar_en(self):
        self.assertEqual(pages_bazi.lunar_en("二〇二三年闰二月廿一"), "year 2023, leap month 2, day 21")
        self.assertEqual(pages_bazi.lunar_en("一九九〇年腊月三十"), "year 1990, month 12, day 30")
        self.assertEqual(pages_bazi.lunar_en("二〇〇一年正月初十"), "year 2001, month 1, day 10")
        self.assertEqual(pages_bazi.lunar_en("二〇〇一年冬月十五"), "year 2001, month 11, day 15")

    def test_relations_cover_every_kind(self):
        from kanyu.ganzhi import JIAZI
        natal = ["庚午", "辛巳", "丁酉", "甲辰"]
        for gz in JIAZI:
            self.assertEnglish(pages_bazi.against_natal_en(gz, natal, "Year"))

    def test_cli(self):
        with tempfile.TemporaryDirectory() as td:
            cwd = os.getcwd()
            os.chdir(td)
            try:
                out, _ = cli.run(["bazi", "--birth", "1990-06-01 08:30", "--gender", "f", "--lang", "en", "--html"])
            finally:
                os.chdir(cwd)
            self.assertTrue(out.data["html"].endswith("bazi-chart-gengwu-xinsi-dingyou-jiachen.html"))
            with open(out.data["html"], encoding="utf-8") as f:
                self.assertIn('<html lang="en">', f.read())
        with self.assertRaises(cli.UsageError):
            cli.run(["bazi", "--birth", "1990-06-01 08:30", "--gender", "f", "--lang", "en"])


if __name__ == "__main__":
    unittest.main()
