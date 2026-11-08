"""交互盘面：数据与排盘一致、批注安全嵌入、CLI 生成文件。"""

import support  # noqa: F401
import json
import os
import tempfile
import unittest

from kanyu import cli, pages
from kanyu.feixing import feixing_chart

NOTES = {"summary": "总断 </script><b>不应被当作标签</b>",
         "palaces": {"离": "向首批注", "坎": "坐山批注"}, "advice": ["建议一"]}


def page_for(ch, notes=None, **kw):
    data = pages.feixing_data(ch, annual=kw.get("annual"), annual_label=None, month=None,
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
        self.assertEqual((d["title"], d["subtitle"]), ("子山午向", "八运宅"))
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
            self.assertEqual(pages.load_notes(write(NOTES)), NOTES)
            for bad in ({"palace": {}}, {"palaces": {"南": "x"}}, {"advice": [1]}, ["x"]):
                with self.assertRaises(ValueError, msg=bad):
                    pages.load_notes(write(bad))


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

    def test_example_page_is_current(self):
        # docs/examples 中的示例页面须与当前模板一致（修改模板后重新生成）
        root = support.ROOT
        with open(os.path.join(root, "docs", "examples", "feixing-demo.html"), encoding="utf-8") as f:
            demo = f.read()
        with open(os.path.join(root, "assets", "templates", "feixing.html"), encoding="utf-8") as f:
            tpl = f.read()
        head = tpl.split("__DATA__")[0].replace("__TITLE__", "飞星盘 子山午向")
        self.assertTrue(demo.startswith(head), "示例页面已过期：重新运行 docs/examples/README 中的命令")


if __name__ == "__main__":
    unittest.main()
