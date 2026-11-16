"""由维基文库《窮通寶鑑》wikitext 生成「日干 × 月令」调候原文索引。

用法：python3 -I build_qiongtong.py <窮通寶鑑.wiki> <输出 json>
原文先用 fetch_wikisource.py（任务行：`raw 窮通寶鑑`）下载。

每格收：
- 该月专论段落（段首为「正月甲木」「正二月甲木」「七月戊土」之类；合论段如「正二月」「十一二月」两月共用）；
- 季节总论段（段首为「三春戊土」「冬月之木」之类），点名本月时收入；没有专论段时收总论首段。
不提炼「用某某」之类标签：那是后世评注本的概括，不是原书文字。
生成后须人工逐格核对（tests/test_qiongtong.py 抽查关键格）。
"""
import json
import re
import sys

GAN = "甲乙丙丁戊己庚辛壬癸"
WX = dict(zip(GAN, "木木火火土土金金水水"))
SEASON_ZHI = {"春": "寅卯辰", "夏": "巳午未", "秋": "申酉戌", "冬": "亥子丑"}
MONTH_ZHI = dict(zip(["正", "二", "三", "四", "五", "六", "七", "八", "九", "十", "十一", "十二"],
                     "寅卯辰巳午未申酉戌亥子丑"))
ZHI_MONTH = {v: k for k, v in MONTH_ZHI.items()}
# 段首月份（长者优先）：「十一二月」= 子丑，「正二月」= 寅卯，「五六月」= 午未
HEAD = re.compile(r"^(十一二|十一|十二|正二|五六|正|十|[二三四五六七八九])月(之([甲乙丙丁戊己庚辛壬癸])|([甲乙丙丁戊己庚辛壬癸])[木火土金水])?")
MULTI = {"十一二": "子丑", "正二": "寅卯", "五六": "午未"}


def clean(s: str) -> str:
    s = re.sub(r"\{\{PUA\|[^}]*\}\}", "□", s)       # 维基文库标注的缺字
    s = re.sub(r"<[^>]+>", "", s).replace("'''", "")
    return s.strip()


def month_named(text: str, zhi: str) -> bool:
    m = ZHI_MONTH[zhi]
    pats = {"正": r"正二?月", "二": r"(?<!十)(?<!十一)二月", "十": r"十月",
            "十一": r"十一二?月", "十二": r"十二月|十一二月"}
    return re.search(pats.get(m, m + r"月"), text) is not None


def build(wiki: str) -> dict:
    lines = wiki.splitlines()
    gan = season = None
    sections: dict[tuple[str, str], list[tuple[int, str]]] = {}
    for no, raw in enumerate(lines, 1):
        h = re.match(r"^(=+)\s*(.+?)\s*=+$", raw)
        if h:
            title = h.group(2)
            m = re.match(r"^论([甲乙丙丁戊己庚辛壬癸])[木火土金水]$", title)
            if m:
                gan, season = m.group(1), None
            m = re.match(r"^三([春夏秋冬])([甲乙丙丁戊己庚辛壬癸])[木火土金水]$", title)
            if m:
                assert m.group(2) == gan, (no, title)
                season = m.group(1)
            elif len(h.group(1)) <= 2:
                season = None
            continue
        if gan and season and raw.strip():
            sections.setdefault((gan, season), []).append((no, raw))

    out = {}
    for (gan, season), paras in sections.items():
        heads, general = [], []   # 专论/合论：(行号, 覆盖月支, 原文)；季论：(行号, 原文)
        for no, raw in paras:
            text = clean(raw)
            if re.match(rf"^(凡)?(三{season}|{season}月之)", text) or (no == paras[0][0] and not HEAD.match(text)):
                general.append((no, text))
                continue
            m = HEAD.match(text)
            if not m:
                continue
            g = m.group(3) or m.group(4)
            if g and g != gan:
                continue
            if not raw.lstrip().startswith("'''") and not g:   # 「八月支成金局……」之类条件句，不作专论段
                continue
            key = m.group(1)
            heads.append((no, MULTI.get(key, MONTH_ZHI.get(key)), text))
        for zhi in SEASON_ZHI[season]:
            passages = [{"line": no, "kind": "合论" if len(z) > 1 else "专论", "text": t}
                        for no, z, t in heads if zhi in z]
            named = [(no, t) for no, t in general if month_named(t, zhi)]
            seasonal = sorted(set(named + ([] if passages else general[:1])))
            passages = [{"line": no, "kind": "季论", "text": t} for no, t in seasonal] + passages
            out[gan + zhi] = {
                "gan": gan, "month_zhi": zhi, "month": ZHI_MONTH[zhi] + "月",
                "section": f"论{gan}{WX[gan]} · 三{season}{gan}{WX[gan]}",
                "passages": passages,
            }
    return out


def main():
    with open(sys.argv[1], encoding="utf-8") as f:
        data = build(f.read())
    missing = [g + z for g in GAN for z in "寅卯辰巳午未申酉戌亥子丑" if not data.get(g + z, {}).get("passages")]
    if missing:
        sys.exit(f"缺格：{missing}")
    ordered = {g + z: data[g + z] for g in GAN for z in "寅卯辰巳午未申酉戌亥子丑"}
    doc = {
        "source": "《穷通宝鉴》，维基文库「窮通寶鑑」页（wikitext），行号即该页原文行号",
        "url": "https://zh.wikisource.org/wiki/窮通寶鑑",
        "note": "月令以节气月为准（正月=寅月）。专论 = 该月专段；合论 = 两月共用一段；季论 = 三春/三夏/三秋/三冬总论首段。"
                "□ 为维基文库标注的缺字。只录原文，不作概括。",
        "cells": ordered,
    }
    with open(sys.argv[2], "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=1)
        f.write("\n")


if __name__ == "__main__":
    main()
