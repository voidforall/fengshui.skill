"""命令行层：快照（golden）测试 + JSON + 出错路径 + 入口脚本。

快照：tests/golden/cases.tsv 每行「名称<TAB>参数」，期望输出为 golden/<名称>.txt。
有意修改输出格式后，用 UPDATE_GOLDEN=1 重新生成并审阅 diff：
    UPDATE_GOLDEN=1 python3 -m unittest discover -s tests
"""

import support
import datetime as dt
import json
import os
import shlex
import subprocess
import sys
import unittest
from unittest import mock

from kanyu import cli

FIXED_TODAY = dt.date(2026, 11, 4)


def run_text(args: str) -> str:
    with mock.patch.object(cli, "today", return_value=FIXED_TODAY):
        out, _ = cli.run(shlex.split(args))
    return out.text


def load_cases():
    with open(os.path.join(support.GOLDEN, "cases.tsv"), encoding="utf-8") as f:
        return [line.rstrip("\n").split("\t", 1) for line in f if line.strip()]


@support.needs_lunar
class TestGolden(unittest.TestCase):
    def test_golden(self):
        update = os.environ.get("UPDATE_GOLDEN")
        for name, args in load_cases():
            with self.subTest(name):
                path = os.path.join(support.GOLDEN, f"{name}.txt")
                got = run_text(args) + "\n"
                if update:
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(got)
                    continue
                with open(path, encoding="utf-8") as f:
                    self.assertEqual(got, f.read())


class TestPure(unittest.TestCase):
    """不依赖历法库的命令也必须能跑。"""

    def test_feixing_without_today_dependency(self):
        with mock.patch.object(cli, "today", return_value=dt.date(2030, 1, 1)):
            a, _ = cli.run(["feixing", "--facing", "180", "--yun", "8"])
        with mock.patch.object(cli, "today", return_value=dt.date(2010, 1, 1)):
            b, _ = cli.run(["feixing", "--facing", "180", "--yun", "8"])
        self.assertIn("当前为9运", a.text)
        self.assertNotIn("当前为", b.text)

    def test_liunian(self):
        self.assertIn("【2026 丙午年】中宫 一白贪狼", run_text("liunian --year 2026"))

    def test_bazhai_match(self):
        t = run_text("bazhai --facing 卯 --birth 1988-05-01 --gender m")
        self.assertIn("兑宅（西四宅）", t)
        self.assertIn("震卦，东四命", t)
        self.assertIn("不配", t)


class TestJson(unittest.TestCase):
    def test_feixing_json(self):
        out, _ = cli.run(["feixing", "--facing", "180", "--yun", "8", "--json"])
        d = json.loads(json.dumps(cli._jsonable(out.data), ensure_ascii=False))
        self.assertEqual(d["chart"]["shan"]["离"], 8)
        self.assertEqual(d["chart"]["xiang"]["离"], 8)
        self.assertEqual(d["chart"]["shan_entry"]["by"], "巽")

    def test_mingua_json(self):
        out, _ = cli.run(["mingua", "--birth", "1990-06-01", "--gender", "f"])
        d = cli._jsonable(out.data)
        self.assertEqual((d["number"], d["gua"], d["jigong"]), (8, "艮", "女命五寄艮"))
        self.assertEqual(d["younian"]["生气"], "坤")


class TestErrors(unittest.TestCase):
    def test_usage(self):
        for args in (["feixing", "--facing", "午"], ["feixing", "--yun", "8"], ["bazhai"]):
            with self.assertRaises(cli.UsageError):
                cli.run(args)

    def test_value(self):
        for args in (["feixing", "--facing", "xx", "--yun", "9"],
                     ["mingua", "--birth", "1990", "--gender", "x"]):
            with self.assertRaises(ValueError):
                cli.run(args)


class TestEntryScript(unittest.TestCase):
    def test_subprocess(self):
        script = os.path.join(support.SCRIPTS, "fengshui.py")
        r = subprocess.run([sys.executable, script, "feixing", "--facing", "180", "--yun", "8"],
                           capture_output=True, text=True, cwd="/")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("双星到向", r.stdout)
        r = subprocess.run([sys.executable, script, "feixing", "--facing", "xx", "--yun", "8"],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 1)
        self.assertIn("错误", r.stderr)


if __name__ == "__main__":
    unittest.main()
