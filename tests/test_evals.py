"""eval 框架自检（不调用模型）：案例文件合法、判分解析与汇总逻辑正确。"""

import support
import importlib.util
import os
import re
import unittest

spec = importlib.util.spec_from_file_location("eval_run", os.path.join(support.ROOT, "evals", "run.py"))
run = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run)

GZ = r"[甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥]"


class TestCases(unittest.TestCase):
    def setUp(self):
        self.cases = run.load_cases()

    def test_count_and_categories(self):
        self.assertGreaterEqual(len(self.cases), 20)
        self.assertEqual({c["category"] for c in self.cases} - {"八字", "形势", "年神", "诚实边界"}, set())

    def test_pillars_appear_in_quote(self):
        # 命例题：题目中的四柱必须出现在原文引文里（或原文为阐微命例，四柱在命例数据中）
        import json
        with open(os.path.join(support.ROOT, "tests", "data", "ditiansui_dayun.json"), encoding="utf-8") as f:
            dts = {c["id"]: c["pillars"] for c in json.load(f)["cases"]}
        for c in self.cases:
            p = re.findall(GZ, c["prompt"])
            if len(p) < 4:
                continue
            if c["id"] in dts:
                self.assertEqual(p[:4], dts[c["id"]], c["id"])
            else:
                self.assertEqual(re.findall(GZ, c["source"]["quote"])[:4], p[:4], c["id"])

    def test_sources_registered(self):
        with open(os.path.join(support.ROOT, "references", "sources.md"), encoding="utf-8") as f:
            reg = f.read()
        for c in self.cases:
            for title in re.findall(r"《([^》·]+)", c["source"]["book"]):
                if c["category"] in ("形势", "年神", "诚实边界"):
                    continue   # 转引自《古今图书集成》，已登记
                self.assertIn(title, reg, c["id"])


class TestHelpers(unittest.TestCase):
    def test_parse_verdict(self):
        self.assertEqual(run.parse_verdict('{"verdict": "一致", "reason": "x"}')["verdict"], "一致")
        self.assertEqual(run.parse_verdict('好的\n{"verdict":"部分一致","reason":"y"}')["verdict"], "部分一致")
        self.assertEqual(run.parse_verdict("无法判断")["verdict"], "无法判分")
        self.assertEqual(run.parse_verdict('{"verdict": "大概"}')["verdict"], "无法判分")

    def test_keyword_check(self):
        self.assertTrue(run.keyword_check("用神在午火", ["午", "火"])["pass"])
        self.assertEqual(run.keyword_check("用神在木", ["火"])["missing"], ["火"])

    def test_summarize(self):
        rs = [{"id": "a", "category": "八字", "judge": {"verdict": "一致", "reason": "r"},
               "keywords": {"pass": True, "missing": []}, "used_skill": True, "used_script": False, "cost_usd": 0.5}]
        md = run.summarize(rs, {"time": "t", "model": None, "judge_model": None})
        self.assertIn("| 八字 | 1 | 0 | 0 | 0 | 1/1 | 1/1 |", md)

    def test_workspace_has_skill(self):
        ws = run.make_workspace()
        try:
            self.assertTrue(os.path.exists(os.path.join(ws, ".claude", "skills", "fengshui-master", "SKILL.md")))
            self.assertTrue(os.path.exists(os.path.join(ws, ".claude", "skills", "fengshui-master", "scripts", "fengshui.py")))
        finally:
            import shutil
            shutil.rmtree(ws)


if __name__ == "__main__":
    unittest.main()
