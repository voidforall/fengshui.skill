"""可交互 HTML 页面：把排盘结果填进模板，生成单个离线可用的 HTML 文件。

图形与数据全部来自计算模块；模型的解读通过 notes（JSON）传入，只作为文字嵌入页面。
模板见 skill 根目录 assets/templates/。
"""

from __future__ import annotations

import datetime as _dt
import json
import os
import re

from . import __version__
from . import render as text
from .bazi import Bazi, liunian
from .ganzhi import changsheng
from .core import (GRID, LUOSHU_PATH, MOUNTAINS, PALACE_DIR, PALACES, STAR_NAMES,
                   deg_to_mountain, fly, mountain_center_deg, mountain_yinyang, wuxing_of)
from .feixing import Chart, jian_warnings, main_pattern, palace_flags, star_status

# 模板放在 skill 根目录的 assets/templates/（Agent Skills 规范：模板等静态资源放 assets/）
SKILL_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
TEMPLATES = os.path.join(SKILL_ROOT, "assets", "templates")

# 《周易·说卦传》第十、十一章取象（原文已核对，见 references/sources.md）
GUA_XIANG = {
    "乾": "乾为天、为圜、为君、为父、为玉、为金",
    "坤": "坤为地、为母、为布、为釜、为均、为众",
    "震": "震为雷、为龙、为长子、为大涂、为决躁",
    "巽": "巽为木、为风、为长女、为绳直、为工、为高",
    "坎": "坎为水、为沟渎、为隐伏、为中男",
    "离": "离为火、为日、为电、为中女、为甲胄",
    "艮": "艮为山、为径路、为小石、为门阙、为少男",
    "兑": "兑为泽、为少女、为巫、为口舌、为毁折",
}
GUA_DEG = {"坎": 0, "艮": 45, "震": 90, "巽": 135, "离": 180, "坤": 225, "兑": 270, "乾": 315}

NOTES_KEYS = {"summary", "palaces", "advice"}


def load_notes(path: str | None) -> dict:
    """读取模型写的批注 JSON：{"summary": str, "palaces": {宫名: str}, "advice": [str]}。"""
    if not path:
        return {}
    with open(path, encoding="utf-8") as f:
        notes = json.load(f)
    if not isinstance(notes, dict):
        raise ValueError("notes 应为 JSON 对象")
    unknown = set(notes) - NOTES_KEYS
    if unknown:
        raise ValueError(f"notes 含未知字段：{'、'.join(sorted(unknown))}（可用：summary、palaces、advice）")
    pals = notes.get("palaces", {})
    bad = set(pals) - set(PALACE_DIR)
    if bad:
        raise ValueError(f"notes.palaces 的键应为宫名（坎坤震巽中乾兑艮离），收到：{'、'.join(sorted(bad))}")
    if not all(isinstance(v, str) for v in pals.values()) or not isinstance(notes.get("summary", ""), str) \
            or not all(isinstance(a, str) for a in notes.get("advice", [])):
        raise ValueError("notes 中的批注应为文字")
    return notes


def _embed_json(data) -> str:
    # 防止批注文字中的 </script> 截断脚本
    return json.dumps(data, ensure_ascii=False).replace("</", "<\\/")


def _escape_html(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def feixing_data(ch: Chart, *, annual: int | None, annual_label: str | None, month: int | None,
                 facing_deg: float | None, yun_note: str, current_yun: int, notes: dict) -> dict:
    ann = fly(annual) if annual else None
    mon = fly(month) if month else None
    palaces = {}
    for p in LUOSHU_PATH:
        palaces[p] = {
            "dir": PALACE_DIR[p],
            "xiang": GUA_XIANG.get(p, ""),
            "flags": palace_flags(ch.shan[p], ch.xiang[p], ann[p] if ann else None),
        }
    facts = [("元运", f"{NUM_CN[ch.yun]}运"), ("坐向", f"坐{ch.sit}向{ch.facing}"),
             ("排法", "替卦" if ch.tigua else "下卦")]
    warnings = []
    axis = facing_deg if facing_deg is not None else mountain_center_deg(ch.facing)
    if facing_deg is not None:
        _, off = deg_to_mountain((facing_deg + 180) % 360)
        facts.append(("罗盘", f"向 {facing_deg:.1f}°（偏{ch.sit}山中线 {off:+.1f}°）"))
        warnings = [w.lstrip("⚠ ").replace("（--tigua）", "") for w in jian_warnings(ch.sit, off)]
    if annual:
        facts.append(("流年", f"{annual_label or ''}{NUM_CN[annual]}入中".strip()))
    if month:
        facts.append(("流月", f"{NUM_CN[month]}入中"))
    entries = []
    for label, e in (("山星", ch.shan_entry), ("向星", ch.xiang_entry)):
        why = f"依{e.by}山（{mountain_yinyang(e.by)}）" if e.n != 5 else f"五入中依{e.by}山本身（{mountain_yinyang(e.by)}）"
        line = f"{label}：运盘{NUM_CN[e.n]}入中，{why}{'顺' if e.forward else '逆'}飞"
        if e.replaced:
            line += f"，替卦以{NUM_CN[e.center]}代之"
        entries.append(line)
    mountains = [{"name": m, "deg": mountain_center_deg(m), "boundary": i % 3 == 0}
                 for i, m in enumerate(MOUNTAINS)]
    return {
        "title": f"{NUM_CN[ch.yun]}运 · {ch.sit}山{ch.facing}向",
        "facts": facts, "warnings": warnings, "yun_note": yun_note,
        "sit": ch.sit, "facing": ch.facing, "sit_palace": ch.sit_palace, "face_palace": ch.face_palace,
        "axis_deg": axis,
        "patterns": ch.patterns, "main_pattern": main_pattern(ch),
        "entries": entries,
        "layers": {"yun": ch.yunpan, "shan": ch.shan, "xiang": ch.xiang, "annual": ann, "month": mon},
        "current_yun": current_yun, "current_yun_cn": NUM_CN[current_yun], "yun_cn": NUM_CN[ch.yun],
        "status": {n: star_status(n, current_yun) for n in range(1, 10)},
        "chart_status": ({n: star_status(n, ch.yun) for n in range(1, 10)} if ch.yun != current_yun else None),
        "star_names": STAR_NAMES,
        "palaces": palaces, "grid": GRID, "path": LUOSHU_PATH,
        "mountains": mountains,
        "gua_ring": [{"name": g, "deg": GUA_DEG[g]} for g in PALACES],
        "notes": notes,
        "autoplay": True,
        "source": f"堪舆子 fengshui-master v{__version__} · 生成于 {_dt.date.today():%Y-%m-%d} · "
                  f"盘面由 scripts/fengshui.py 计算，旺衰按当前{NUM_CN[current_yun]}运论",
    }


NUM_CN = ["", "一", "二", "三", "四", "五", "六", "七", "八", "九"]


def render(template: str, title: str, data: dict) -> str:
    with open(os.path.join(TEMPLATES, template), encoding="utf-8") as f:
        tpl = f.read()
    return tpl.replace("__TITLE__", _escape_html(title)).replace("__DATA__", _embed_json(data))


def default_name(ch: Chart) -> str:
    return f"飞星盘-{ch.yun}运-{ch.sit}山{ch.facing}向.html"


def write_page(path: str, html: str) -> str:
    path = os.path.abspath(path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    return path


def extract_data(html: str) -> dict:
    """从生成的页面中取回嵌入的数据（测试用）。"""
    m = re.search(r'<script id="chart-data" type="application/json">(.*?)</script>', html, re.S)
    return json.loads(m.group(1).replace("<\\/", "</"))



# --- 八字命盘 --------------------------------------------------------------------

BAZI_NOTES_KEYS = {"summary", "basis", "pillars", "dayun", "years", "advice"}


def load_bazi_notes(path: str | None) -> dict:
    """读取八字批注 JSON：{"summary", "basis": str, "pillars": {年|月|日|时: str},
    "dayun": {大运干支: str}, "years": {"2026": str}, "advice": [str]}。"""
    if not path:
        return {}
    with open(path, encoding="utf-8") as f:
        notes = json.load(f)
    if not isinstance(notes, dict):
        raise ValueError("notes 应为 JSON 对象")
    unknown = set(notes) - BAZI_NOTES_KEYS
    if unknown:
        raise ValueError(f"notes 含未知字段：{'、'.join(sorted(unknown))}（可用：{'、'.join(sorted(BAZI_NOTES_KEYS))}）")
    for k in ("summary", "basis"):
        if not isinstance(notes.get(k, ""), str):
            raise ValueError(f"notes.{k} 应为文字")
    for k, keys in (("pillars", set("年月日时")), ("dayun", None), ("years", None)):
        v = notes.get(k, {})
        if not isinstance(v, dict) or not all(isinstance(x, str) for x in v.values()):
            raise ValueError(f"notes.{k} 应为 {{键: 文字}}")
        if keys is not None and set(v) - keys:
            raise ValueError(f"notes.pillars 的键应为 年、月、日、时，收到：{'、'.join(sorted(set(v) - keys))}")
        if k == "years" and not all(x.isdigit() for x in v):
            raise ValueError("notes.years 的键应为年份，如 \"2026\"")
        if k == "dayun" and not all(len(x) == 2 for x in v):
            raise ValueError("notes.dayun 的键应为大运干支，如 \"甲申\"")
    if not isinstance(notes.get("advice", []), list) or not all(isinstance(a, str) for a in notes.get("advice", [])):
        raise ValueError("notes.advice 应为文字列表")
    return notes


def bazi_title(b: Bazi) -> str:
    return f"{'乾造' if b.gender == 'm' else '坤造'} {' '.join(b.ganzhi)}"


def bazi_default_name(b: Bazi) -> str:
    return f"八字命盘-{''.join(b.ganzhi)}.html"


def _rel_short(r: dict) -> str:
    """弧线上的短标签。"""
    if r["kind"] in ("三合", "三会"):
        return f"{r['kind']}{r['wuxing']}"
    if r["kind"] == "三合缺一":
        return f"缺{r['missing']}"
    return r["label"].split(" ")[-1]


def bazi_data(b: Bazi, *, notes: dict) -> dict:
    m = b.moment
    pillars = []
    for p, r in zip(b.pillars, b.roots):
        pillars.append({
            "name": p.name, "gz": p.ganzhi, "gan": p.gan, "zhi": p.zhi,
            "gan_wx": wuxing_of(p.gan), "zhi_wx": wuxing_of(p.zhi),
            "gan_yy": "阳" if p.gan in "甲丙戊庚壬" else "阴", "zhi_yy": "阳" if p.zhi in "子寅辰午申戌" else "阴",
            "gan_ss": p.gan_shishen, "nayin": p.nayin, "changsheng": p.changsheng, "xunkong": p.xunkong,
            "zizuo": changsheng(p.gan, p.zhi),
            "hidden": [{"gan": h.gan, "qi": h.qi, "ss": h.shishen, "wx": wuxing_of(h.gan)} for h in p.hidden],
            "roots": r["roots"],
            "tou": [t for t in b.tou if t["pillar"] == p.name],
            "shensha": [x["name"] for x in b.shensha if any(h.startswith(p.name) for h in x["hits"])],
        })
    idx = {n: i for i, n in enumerate("年月日时")}

    def rel(rs):
        return [{"kind": r["kind"], "label": r["label"], "at": [idx[x[0]] for x in r["members"]],
                 "short": _rel_short(r)} for r in rs]

    dayun = [{
        "gz": dy.ganzhi, "start": f"{dy.start:%Y-%m}", "start_year": dy.start.year, "age": text._age(*dy.start_age),
        "age_short": f"{dy.start_age[0]}岁" + (f"{dy.start_age[1]}月" if dy.start_age[1] else ""),
        "gan_ss": dy.gan_shishen, "zhi_ss": dy.zhi_shishen, "cs": dy.changsheng, "relations": dy.relations,
        "gan_wx": wuxing_of(dy.ganzhi[0]), "zhi_wx": wuxing_of(dy.ganzhi[1]),
        "years": [{"year": y.year, "gz": y.ganzhi, "age": y.age, "ss": y.gan_shishen, "cs": y.changsheng,
                   "relations": y.relations} for y in dy.years],
    } for dy in b.dayun]
    pre = []   # 起运前的流年
    for y in range(m.clock.year, b.dayun[0].start.year):
        ln = liunian(y, b.ganzhi, b.day_gan, m.clock.year)
        pre.append({"year": y, "gz": ln.ganzhi, "age": ln.age, "ss": ln.gan_shishen, "cs": ln.changsheng,
                    "relations": ln.relations})
    s = b.siling
    facts = [("出生", f"{m.clock:%Y-%m-%d}" + (f" {m.clock:%H:%M}" if m.time_known else "（时辰不详）")),
             ("农历", b.lunar), ("时区", m.tz)]
    if m.solar is not None:
        facts.append(("真太阳时", f"{m.solar:%H:%M}（经度 {m.longitude}°）"))
    if m.time_known:
        facts.append(("子时", "23:00 换日" if b.zi_rule == "next" else "晚子不换日"))
    facts.append(("起运", f"{b.qiyun[0]}年{b.qiyun[1]}月{b.qiyun[2]}天（{b.qiyun_date:%Y-%m-%d}）"))
    facts.append(("命卦", f"{b.mingua.gua}卦 · {b.mingua.group}命"))
    return {
        "title": bazi_title(b), "gender": "乾造" if b.gender == "m" else "坤造",
        "day_gan": b.day_gan, "day_wx": wuxing_of(b.day_gan),
        "day_yy": "阳" if b.day_gan in "甲丙戊庚壬" else "阴",
        "month_zhi": b.month_zhi, "time_known": m.time_known,
        "facts": facts, "warnings": b.warnings, "time_lines": [t for t in text.bazi_time(b)[1:] if not t.startswith("⚠")],
        "pillars": pillars,
        "relations": {"gan": rel(b.relations["gan"]), "zhi": rel(b.relations["zhi"])},
        "wuxing": {"count": b.wuxing_count, "hidden": b.wuxing_hidden},
        "siling": {"jie": s["jie"], "day_n": s["day_n"], "ruler": s["ruler"],
                   "jie_time": f"{s['jie_time']:%Y-%m-%d %H:%M}", "table": s["table"]},
        "tiaohou": b.tiaohou,
        "shensha": b.shensha,
        "dayun": dayun, "pre_years": pre,
        "birth_year": m.clock.year, "focus_year": b.focus_year,
        "today_year": _dt.date.today().year,
        "notes": notes,
        "source": f"bazi-mingli · 计算库 kanyu v{__version__} · 生成于 {_dt.date.today():%Y-%m-%d} · "
                  "排盘与查表由 scripts/bazi.py 计算；批注为解读，非计算结果",
    }
