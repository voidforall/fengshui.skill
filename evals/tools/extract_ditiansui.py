"""从维基文库《滴天髓阐微》原文（wikitext）抽取命例：四柱、大运、所在章节、任氏分析。

用法：python3 -I extract_ditiansui.py <滴天髓闡微.wiki> <输出.json>

书中命例格式：四柱各占一行，其后为大运若干步（时柱与第一步大运偶有同行，如「壬申己酉」）。
只收录大运序列逐步相邻、且首步与月柱相邻的命例；其余记入 rejected 供人工复核。
"""

import json
import re
import sys

GAN = "甲乙丙丁戊己庚辛壬癸"
ZHI = "子丑寅卯辰巳午未申酉戌亥"
GZ = re.compile(f"[{GAN}][{ZHI}]")
GZ_LINE = re.compile(rf"^\s*(?:[{GAN}][{ZHI}]\s*)+$")
JIAZI = [GAN[i % 10] + ZHI[i % 12] for i in range(60)]


def step(a: str, b: str) -> int:
    d = (JIAZI.index(b) - JIAZI.index(a)) % 60
    return {1: 1, 59: -1}.get(d, 0)


def clean(s: str) -> str:
    s = re.sub(r"\{\{[^{}|]*\|", "", s)      # {{annotate|…}} 等模板头
    s = s.replace("}}", "").replace("{{", "")
    return re.sub(r"\s+", "", s)


def main(src, out):
    lines = open(src, encoding="utf-8").read().splitlines()
    heads = []           # (行号, 章, 节)
    chap = sec = ""
    for i, l in enumerate(lines):
        m = re.match(r"^(=+)\s*([^=]+?)\s*=+\s*$", l)
        if m:
            if len(m.group(1)) == 2:
                chap, sec = m.group(2), ""
            elif len(m.group(1)) == 3:
                sec = m.group(2)
        heads.append((chap, sec))

    cases, rejected = [], []
    i = 0
    while i < len(lines):
        if not GZ_LINE.match(lines[i]):
            i += 1
            continue
        start, toks = i, []
        while i < len(lines) and (GZ_LINE.match(lines[i]) or not lines[i].strip()):
            toks += GZ.findall(lines[i])
            i += 1
        if len(toks) < 8:
            continue
        pillars, dayun = toks[:4], toks[4:]
        # 分析文字：其后第一段非空正文
        j = i
        while j < len(lines) and not lines[j].strip():
            j += 1
        analysis = clean(lines[j]) if j < len(lines) else ""
        chap, sec = heads[start]
        steps = {step(a, b) for a, b in zip(dayun, dayun[1:])}
        first = step(pillars[1], dayun[0])
        rec = {"line": start + 1, "chapter": chap, "section": sec,
               "pillars": pillars, "dayun": dayun, "analysis": analysis}
        if len(steps) == 1 and 0 not in steps and first == steps.pop():
            rec["direction"] = "顺" if first == 1 else "逆"
            cases.append(rec)
        else:
            rec["reason"] = "大运不连续或首步不接月柱"
            rejected.append(rec)

    for n, c in enumerate(cases, 1):
        c["id"] = f"dts-{n:03d}"
    json.dump({"source": "任铁樵《滴天髓阐微》，维基文库 zh.wikisource.org/wiki/滴天髓闡微",
               "cases": cases, "rejected": rejected},
              open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"cases={len(cases)} rejected={len(rejected)}")


if __name__ == "__main__":
    main(*sys.argv[1:3])
