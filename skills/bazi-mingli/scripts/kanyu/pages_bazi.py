"""八字命盘页面数据（bazi-mingli）。模板 assets/templates/bazi.html。"""

from __future__ import annotations

import datetime as _dt
import json

from . import __version__, glossary
from . import render_bazi as text
from .bazi import Bazi, liunian
from .core import wuxing_of
from .ganzhi import changsheng

BAZI_NOTES_KEYS = {"plain", "summary", "basis", "pillars", "dayun", "years", "advice"}


def load_bazi_notes(path: str | None) -> dict:
    """读取八字批注 JSON：{"plain": 白话总结, "summary", "basis": str, "pillars": {年|月|日|时: str},
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
    for k in ("plain", "summary", "basis"):
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
        "wangxiang": b.wangxiang,
        "glossary": glossary.page_data(),
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
