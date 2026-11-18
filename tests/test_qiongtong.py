"""《穷通宝鉴》调候原文索引：120 格齐全、月令对应正确、与 eval 所引原文一致。

索引由 evals/tools/build_qiongtong.py 从维基文库原文生成，此处抽查人工核对过的关键格。
"""

import support
import json
import os
import unittest

from kanyu.bazi import tiaohou
from kanyu.core import GAN

ZHI_ORDER = "寅卯辰巳午未申酉戌亥子丑"
MONTHS = ["正", "二", "三", "四", "五", "六", "七", "八", "九", "十", "十一", "十二"]


class TestQiongtong(unittest.TestCase):
    def test_complete(self):
        for g in GAN:
            for z, m in zip(ZHI_ORDER, MONTHS):
                t = tiaohou(g, z)
                self.assertEqual(t["month"], m + "月")
                self.assertTrue(t["passages"], g + z)
                for p in t["passages"]:
                    self.assertIn(p["kind"], ("专论", "合论", "季论"))
                    self.assertNotIn("'''", p["text"])

    def test_spot_checks(self):
        self.assertTrue(tiaohou("甲", "寅")["passages"][0]["text"].startswith("正月甲木，初春尚有余寒，得丙癸逢，富贵双全"))
        self.assertTrue(tiaohou("甲", "辰")["passages"][0]["text"].startswith("三月甲木，木气相竭。先取庚金，次用壬水"))
        self.assertTrue(tiaohou("甲", "巳")["passages"][0]["text"].startswith("四月甲木退气，丙火司权，先癸后丁"))
        # 合论：「十一二月」两月共用；「五六月甲木」
        self.assertEqual([p["kind"] for p in tiaohou("戊", "子")["passages"]], ["合论"])
        self.assertEqual(tiaohou("戊", "子")["passages"], tiaohou("戊", "丑")["passages"])
        self.assertTrue(tiaohou("甲", "未")["passages"][0]["text"].startswith("五六月甲木"))
        # 原书无本月专段时取季论：己土夏秋冬、乙木十二月
        self.assertEqual([p["kind"] for p in tiaohou("己", "午")["passages"]], ["季论"])
        self.assertTrue(tiaohou("乙", "丑")["passages"][0]["text"].startswith("冬月之木"))
        # 「六月之丁」写法
        self.assertTrue(tiaohou("丁", "未")["passages"][0]["text"].startswith("六月之丁"))

    def test_matches_eval_quotes(self):
        with open(os.path.join(support.ROOT, "evals", "cases.json"), encoding="utf-8") as f:
            cases = json.load(f)["cases"]
        th = [c for c in cases if c["id"].startswith("qtbj-th")]
        self.assertTrue(th)
        allt = "".join(p["text"] for g in GAN for z in ZHI_ORDER for p in tiaohou(g, z)["passages"])
        for c in th:
            head = c["source"]["quote"][:20]
            self.assertIn(head, allt, c["id"])


if __name__ == "__main__":
    unittest.main()
