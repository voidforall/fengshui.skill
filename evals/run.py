#!/usr/bin/env python3
"""经典案例 eval：用 Claude Code 无头模式跑 skill，再对照古籍结论判分。

    python3 evals/run.py --dry-run                 # 只校验案例、打印题目，不调用模型
    python3 evals/run.py --case dts-001 --case kanyu-taisui
    python3 evals/run.py --category 八字 --model sonnet --jobs 3
    python3 evals/run.py                           # 全部案例

每题两次调用：
  1. 作答：在临时工作区装好本 skill（.claude/skills/fengshui-master），`claude -p` 提问，
     记录工具调用、是否触发 skill、最终回答、花费。
  2. 判分：另起一次 `claude -p`（不给工具），把书中原文、本项目对结论的概括与回答一并给出，
     要求输出 JSON：{"verdict": "一致|部分一致|不一致", "reason": "..."}。
另有不调用模型的规则检查：回答中是否出现案例的关键字（keywords）。

结果写入 evals/results/<时间戳>/：每题一个 JSON、summary.md 汇总。
注意：判分的「标准答案」是古籍的结论，只检验 skill 是否忠实于典籍，不说明命理风水是否灵验。
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import datetime as dt
import json
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CASES = os.path.join(ROOT, "evals", "cases.json")
SKILL_FILES = ["SKILL.md", "scripts", "references", "examples", "requirements.txt"]
VERDICTS = ("一致", "部分一致", "不一致")
ANSWER_TOOLS = ["Skill", "Read", "Glob", "Grep", "Bash(python3:*)", "Bash(python:*)", "Bash(pip install:*)"]

JUDGE_PROMPT = """你是严格的评审。下面是一道命理 / 风水题、古籍中的原文结论，以及被评测助手的回答。
请只判断「回答的核心结论是否与古籍一致」，不评判文笔，也不评判命理风水本身是否灵验。

判定标准：
- 一致：核心结论（如旺衰判断、用神五行、格局、吉凶方向、该不该做）与古籍相同，理由方向相合。
- 部分一致：核心结论一半相同，或结论相同但给出了与古籍相反的关键理由，或含糊两可。
- 不一致：核心结论与古籍相反或不同（例如用神取了古籍明确否定的五行）。

【题目】
{prompt}

【古籍原文】（{book}，{location}）
{quote}

【古籍结论概括】（供参考，如与原文冲突以原文为准）
{expected}

【助手回答】
{answer}

只输出一行 JSON，不要其他文字：{{"verdict": "一致|部分一致|不一致", "reason": "不超过80字"}}"""


# --- 案例 ----------------------------------------------------------------------------

def load_cases() -> list[dict]:
    with open(CASES, encoding="utf-8") as f:
        data = json.load(f)
    cases = data["cases"]
    ids = [c["id"] for c in cases]
    assert len(ids) == len(set(ids)), "案例 id 重复"
    for c in cases:
        for k in ("id", "category", "source", "prompt", "expected", "keywords"):
            assert k in c, f"{c.get('id')} 缺少字段 {k}"
        for k in ("book", "location", "url", "quote"):
            assert c["source"].get(k), f"{c['id']} source 缺少 {k}"
    return cases


def keyword_check(answer: str, keywords: list[str]) -> dict:
    missing = [k for k in keywords if k not in answer]
    return {"pass": not missing, "missing": missing}


# --- 调用 claude ------------------------------------------------------------------------

def make_workspace() -> str:
    ws = tempfile.mkdtemp(prefix="fengshui-eval-")
    dst = os.path.join(ws, ".claude", "skills", "fengshui-master")
    os.makedirs(dst)
    for name in SKILL_FILES:
        src = os.path.join(ROOT, name)
        if os.path.isdir(src):
            shutil.copytree(src, os.path.join(dst, name), ignore=shutil.ignore_patterns("__pycache__"))
        elif os.path.exists(src):
            shutil.copy(src, dst)
    return ws


def run_claude(prompt: str, cwd: str, model: str | None, tools: list[str] | None,
               timeout: int) -> dict:
    cmd = ["claude", "-p", prompt, "--output-format", "stream-json", "--verbose"]
    if tools is not None:
        cmd += ["--allowedTools", *tools] if tools else ["--tools", ""]
    if model:
        cmd += ["--model", model]
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    tool_calls, result = [], {}
    for line in proc.stdout.splitlines():
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        if ev.get("type") == "assistant":
            for part in ev.get("message", {}).get("content", []):
                if part.get("type") == "tool_use":
                    tool_calls.append({"name": part.get("name"), "input": part.get("input")})
        elif ev.get("type") == "result":
            result = ev
    return {"answer": result.get("result", ""), "cost_usd": result.get("total_cost_usd", 0.0),
            "is_error": bool(result.get("is_error")) or proc.returncode != 0,
            "stderr": proc.stderr[-2000:], "tool_calls": tool_calls}


def parse_verdict(text: str) -> dict:
    start, end = text.find("{"), text.rfind("}")
    try:
        v = json.loads(text[start:end + 1])
        if v.get("verdict") in VERDICTS:
            return v
    except (ValueError, json.JSONDecodeError):
        pass
    return {"verdict": "无法判分", "reason": text[:200]}


def run_case(case: dict, args) -> dict:
    ws = make_workspace()
    try:
        ans = run_claude(case["prompt"], ws, args.model, ANSWER_TOOLS, args.timeout)
    finally:
        shutil.rmtree(ws, ignore_errors=True)
    used_skill = any(t["name"] == "Skill" for t in ans["tool_calls"])
    used_script = any(t["name"] == "Bash" and "fengshui.py" in json.dumps(t["input"], ensure_ascii=False)
                      for t in ans["tool_calls"])
    rec = {"id": case["id"], "category": case["category"], "prompt": case["prompt"],
           "source": case["source"], "expected": case["expected"],
           "answer": ans["answer"], "answer_error": ans["is_error"], "stderr": ans["stderr"],
           "tool_calls": ans["tool_calls"], "used_skill": used_skill, "used_script": used_script,
           "keywords": keyword_check(ans["answer"], case["keywords"]), "cost_usd": ans["cost_usd"]}
    if args.no_judge or not ans["answer"]:
        rec["judge"] = {"verdict": "未判分", "reason": "跳过" if args.no_judge else "无回答"}
        return rec
    with tempfile.TemporaryDirectory(prefix="fengshui-judge-") as jd:
        j = run_claude(JUDGE_PROMPT.format(answer=ans["answer"], **case, **case["source"]),
                       jd, args.judge_model, [], args.timeout)
    rec["judge"] = parse_verdict(j["answer"])
    rec["cost_usd"] += j["cost_usd"]
    return rec


# --- 汇总 ----------------------------------------------------------------------------

def summarize(results: list[dict], meta: dict) -> str:
    out = [f"# 经典案例 eval 结果（{meta['time']}）", "",
           f"- 作答模型：{meta['model'] or '默认'}；判分模型：{meta['judge_model'] or '默认'}",
           f"- 案例数：{len(results)}；总花费：${sum(r['cost_usd'] for r in results):.2f}", ""]
    cats = sorted({r["category"] for r in results})
    out += ["| 类别 | 一致 | 部分一致 | 不一致 | 其他 | 关键字通过 | 触发 skill |", "|---|---|---|---|---|---|---|"]
    for cat in cats + ["合计"]:
        rs = results if cat == "合计" else [r for r in results if r["category"] == cat]
        cnt = {v: sum(r["judge"]["verdict"] == v for r in rs) for v in VERDICTS}
        other = len(rs) - sum(cnt.values())
        out.append(f"| {cat} | {cnt['一致']} | {cnt['部分一致']} | {cnt['不一致']} | {other} | "
                   f"{sum(r['keywords']['pass'] for r in rs)}/{len(rs)} | {sum(r['used_skill'] for r in rs)}/{len(rs)} |")
    out += ["", "## 逐题", "", "| 案例 | 类别 | 判分 | 理由 | 关键字 | skill / 脚本 |", "|---|---|---|---|---|---|"]
    for r in results:
        kw = "✓" if r["keywords"]["pass"] else "缺 " + "、".join(r["keywords"]["missing"])
        reason = r["judge"].get("reason", "").replace("|", "／").replace("\n", " ")
        out.append(f"| {r['id']} | {r['category']} | {r['judge']['verdict']} | {reason} | {kw} | "
                   f"{'✓' if r['used_skill'] else '✗'} / {'✓' if r['used_script'] else '✗'} |")
    out += ["", "判分标准是古籍原文的结论，只检验 skill 是否忠实于典籍。"]
    return "\n".join(out) + "\n"


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--case", action="append", help="只跑指定 id（可多次）")
    p.add_argument("--category", action="append", help="只跑指定类别（可多次）")
    p.add_argument("--model", help="作答模型（传给 claude --model）")
    p.add_argument("--judge-model", help="判分模型")
    p.add_argument("--jobs", type=int, default=1, help="并发数")
    p.add_argument("--timeout", type=int, default=600, help="每次调用超时秒数")
    p.add_argument("--no-judge", action="store_true", help="只作答，不判分")
    p.add_argument("--dry-run", action="store_true", help="只校验并列出案例")
    p.add_argument("--out", help="结果目录（默认 evals/results/<时间戳>）")
    args = p.parse_args(argv)

    cases = load_cases()
    if args.case:
        unknown = set(args.case) - {c["id"] for c in cases}
        if unknown:
            sys.exit(f"未知案例：{'、'.join(sorted(unknown))}")
        cases = [c for c in cases if c["id"] in args.case]
    if args.category:
        cases = [c for c in cases if c["category"] in args.category]
    if args.dry_run:
        for c in cases:
            print(f"[{c['id']}] {c['category']}｜{c['source']['book']}\n  问：{c['prompt']}\n  期望：{c['expected']}\n")
        print(f"共 {len(cases)} 题，校验通过。")
        return
    if not shutil.which("claude"):
        sys.exit("找不到 claude 命令：请先安装 Claude Code（https://code.claude.com）")

    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    out_dir = args.out or os.path.join(ROOT, "evals", "results", stamp)
    os.makedirs(out_dir, exist_ok=True)
    results = []
    with cf.ThreadPoolExecutor(max_workers=args.jobs) as ex:
        futs = {ex.submit(run_case, c, args): c["id"] for c in cases}
        for fut in cf.as_completed(futs):
            cid = futs[fut]
            try:
                r = fut.result()
            except Exception as e:  # 单题失败不影响其余
                r = {"id": cid, "category": next(c["category"] for c in cases if c["id"] == cid),
                     "judge": {"verdict": "运行失败", "reason": repr(e)[:200]},
                     "keywords": {"pass": False, "missing": []}, "used_skill": False,
                     "used_script": False, "cost_usd": 0.0}
            results.append(r)
            with open(os.path.join(out_dir, f"{cid}.json"), "w", encoding="utf-8") as f:
                json.dump(r, f, ensure_ascii=False, indent=1)
            print(f"{cid}: {r['judge']['verdict']}  ${r['cost_usd']:.2f}", flush=True)
    order = {c["id"]: i for i, c in enumerate(cases)}
    results.sort(key=lambda r: order[r["id"]])
    meta = {"time": stamp, "model": args.model, "judge_model": args.judge_model}
    with open(os.path.join(out_dir, "summary.md"), "w", encoding="utf-8") as f:
        f.write(summarize(results, meta))
    print(f"\n结果：{out_dir}/summary.md")


if __name__ == "__main__":
    main()
