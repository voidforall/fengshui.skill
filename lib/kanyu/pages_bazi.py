"""八字命盘页面数据（bazi-mingli）。模板 assets/templates/bazi.html。

lang="zh" 或 "en"：英文页面的数据文字在本文件末尾的 english() 里生成，界面文字在模板的字典里；
英文术语一律取自 terms_en.py，白话释义取自 glossary.py 的英文版。
"""

from __future__ import annotations

import datetime as _dt
import json

import re

from . import __version__, glossary, terms_en
from . import ganzhi as gzr
from . import render_bazi as text
from .bazi import ZI_RULES, Bazi, liunian
from .core import wuxing_of
from .ganzhi import changsheng

LANGS = ("zh", "en")

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


def bazi_title(b: Bazi, lang: str = "zh") -> str:
    if lang == "en":
        return f"Bazi Chart · {'Male' if b.gender == 'm' else 'Female'} · {' '.join(gz_en(g) for g in b.ganzhi)}"
    return f"{'乾造' if b.gender == 'm' else '坤造'} {' '.join(b.ganzhi)}"


def bazi_default_name(b: Bazi, lang: str = "zh") -> str:
    if lang == "en":
        return f"bazi-chart-{'-'.join(gz_en(g) for g in b.ganzhi)}.html".lower()
    return f"八字命盘-{''.join(b.ganzhi)}.html"


def _rel_short(r: dict) -> str:
    """弧线上的短标签。"""
    if r["kind"] in ("三合", "三会"):
        return f"{r['kind']}{r['wuxing']}"
    if r["kind"] == "三合缺一":
        return f"缺{r['missing']}"
    return r["label"].split(" ")[-1]


def bazi_data(b: Bazi, *, notes: dict, lang: str = "zh") -> dict:
    if lang not in LANGS:
        raise ValueError(f"lang 应为 {'/'.join(LANGS)}")
    data = _bazi_data(b, notes=notes)
    return english(b, data) if lang == "en" else {"lang": "zh", **data}


def _bazi_data(b: Bazi, *, notes: dict) -> dict:
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


# --- 英文页面 ------------------------------------------------------------------------

_BZ = {zh: en for zh, en, _ in terms_en.BAZI}
_CS_PY = {"长生": "Chang Sheng", "沐浴": "Mu Yu", "冠带": "Guan Dai", "临官": "Lin Guan", "帝旺": "Di Wang",
          "衰": "Shuai", "病": "Bing", "死": "Si", "墓": "Mu", "绝": "Jue", "胎": "Tai", "养": "Yang"}


def py(ch: str) -> str:
    return terms_en.pinyin(ch)


def gz_en(gz: str) -> str:
    return py(gz[0]) + py(gz[1]).lower()           # 甲子 → Jiazi


def wx_en(wx: str) -> str:
    return terms_en.ELEMENTS[wx]


def _pos(name: str, side: str) -> str:
    """年支 → 'Year branch'。"""
    return f"{terms_en.PILLARS[name]} {'stem' if side == '干' else 'branch'}"


def _chars(s: str) -> str:
    return ", ".join(py(c) for c in s)


def relation_label_en(r: dict) -> tuple[str, str]:
    """原局关系的英文 (label, 弧线短标签)。"""
    members = [_pos(m[0], m[1]) for m in r["members"]]
    if r["kind"] in ("三合", "三会"):
        wx = wx_en(r["wuxing"])
        kind = "Three Harmony" if r["kind"] == "三合" else "Directional"
        return f"{_chars(r['chars'])}: {kind} {wx} ({', '.join(members)})", f"{wx} {'trio' if r['kind'] == '三合' else 'dir.'}"
    if r["kind"] == "三合缺一":
        return (f"{_chars(r['chars'])} ({', '.join(members)}): Three Harmony missing {py(r['missing'])}, not formed",
                f"needs {py(r['missing'])}")
    kind = {"合": "combination", "六合": "Six Harmonies", "冲": "clash", "害": "harm", "自刑": "self-punishment",
            "刑": terms_en.XING_KINDS.get(gzr.XING.get(frozenset(r["chars"]), ""), "punishment")}[r["kind"]]
    short = {"合": "combine", "六合": "harmony", "冲": "clash", "害": "harm", "自刑": "self-punish", "刑": "punish"}[r["kind"]]
    a, b = r["members"]
    return f"{_pos(a[0], a[1])} {py(r['chars'][0])} and {_pos(b[0], b[1])} {py(r['chars'][1])}: {kind}", short


def against_natal_en(gz: str, natal: list[str], who: str) -> list[str]:
    """大运 / 流年与原局的关系（英文）。who：Luck Pillar 或 year。"""
    out = []
    for it in gzr.against_natal_items(gz, natal):
        head = f"{who} {'stem' if it['side'] == '干' else 'branch'} {py(it['char'])}"
        if it["kind"] in ("三合", "三会"):
            others = " and ".join(f"{_pos(n, '支')} {py(x)}" for n, x in it["with"])
            kind = "Three Harmony" if it["kind"] == "三合" else "Directional"
            out.append(f"{head} completes a {kind} {wx_en(it['wuxing'])} set with {others}")
            continue
        (n, x), = it["with"]
        target = f"{_pos(n, it['side'])} {py(x)}"
        if it["kind"] == "自刑":
            out.append(f"{head} and {target}: self-punishment")
        elif it["kind"] in terms_en.XING_KINDS:
            out.append(f"{head} punishes {target} ({terms_en.XING_KINDS[it['kind']]})")
        else:
            verb = {"合": "combines with", "六合": "forms a Six Harmonies combination with", "冲": "clashes with",
                    "刑": "punishes", "害": "harms"}[it["kind"]]
            out.append(f"{head} {verb} {target}")
    return out


_CN_NUM = {"〇": 0, "零": 0, "一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}
_LUNAR_MONTH = {"正": 1, "一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9, "十": 10,
                "冬": 11, "十一": 11, "腊": 12, "十二": 12}


def lunar_en(lunar: str) -> str:
    """「一九九〇年五月初九」→ 'year 1990, month 5, day 9'；闰月注明 leap。"""
    y, rest = lunar.split("年", 1)
    mon, day = rest.split("月", 1)
    leap = mon.startswith("闰")
    mon = _LUNAR_MONTH[mon.lstrip("闰")]
    if day.startswith("初"):
        d = 10 if day == "初十" else _CN_NUM[day[1]]
    elif day.startswith("十"):
        d = 10 + _CN_NUM[day[1]]
    elif day.startswith("廿"):
        d = 20 + _CN_NUM[day[1]]
    elif day == "二十":
        d = 20
    else:
        d = 30
    year = "".join(str(_CN_NUM[c]) for c in y)
    return f"year {year}, {'leap ' if leap else ''}month {mon}, day {d}"


ZI_RULES_EN = {"next": "day changes at 23:00 (start of the Zi hour)",
               "same": "late Zi hour (23:00–24:00) keeps the same day pillar; the hour stem follows the next day"}


def _warning_en(w: str) -> str:
    """bazi.warnings 的英文。新增提示时在这里补一条（tests/test_pages.py 覆盖各类提示）。"""
    if w == "时辰不详，不作真太阳时换算":
        return "Birth time unknown: no true solar time correction."
    if w == "时辰不详：起运按当日正午估算，误差约两个月以内":
        return "Birth time unknown: the start of the Luck Pillars is estimated from noon, within about two months."
    m = re.fullmatch(r"(\S+ \S+) 在当地夏令时切换中不存在（钟表拨快的那一小时），请核对出生时间", w)
    if m:
        return f"{m.group(1)} does not exist locally (the hour skipped when clocks went forward). Please check the birth time."
    m = re.fullmatch(r"生于 23 点后，子时换日两派说法并存。本盘取「.+?」：日柱(..)、时柱(..)；另一说「.+?」：日柱(..)、时柱(..)（加 --zi (\w+) 可按此排）", w)
    if m:
        d1, t1, d2, t2, other = m.groups()
        this = "same" if other == "next" else "next"
        return (f"Born after 23:00, where two schools differ on when the day changes. This chart uses "
                f"'{ZI_RULES_EN[this]}': Day {gz_en(d1)}, Hour {gz_en(t1)}. The other view, '{ZI_RULES_EN[other]}', "
                f"gives Day {gz_en(d2)}, Hour {gz_en(t2)}.")
    m = re.fullmatch(r"出生当日交(\S+?)（(\d\d:\d\d) 北京时间），时辰不详时月柱(、年柱)?可能不准", w)
    if m:
        jq, t, year = m.groups()
        return (f"A solar term ({terms_en.JIEQI[jq]}) begins on the birth day at {t} Beijing time; with the birth time "
                f"unknown, the month pillar{' and year pillar' if year else ''} may be wrong.")
    raise ValueError(f"缺少英文提示：{w}")


def _time_lines_en(b: Bazi) -> list[str]:
    m = b.moment
    if not m.time_known:
        return ["Method: only the year, month and day pillars; the year and month pillars are compared with the solar terms at noon."]
    out = []
    if m.dst_minutes:
        out.append(f"Daylight saving time was in force: clock {m.clock:%H:%M} minus {m.dst_minutes} min → "
                   f"local standard time {m.standard:%H:%M}.")
    if m.solar is not None:
        out.append(f"True solar time: {m.solar:%Y-%m-%d %H:%M} (longitude {m.longitude}°, "
                   f"{m.solar_delta:+.1f} min from standard time).")
    else:
        out.append("True solar time: no birthplace longitude, so the hour pillar uses local standard time "
                   "(add the longitude if the birth was near the boundary of a two-hour period).")
    out.append(f"Method: the year and month pillars compare Beijing time {m.beijing:%Y-%m-%d %H:%M} with the Start "
               f"of Spring and the solar terms; the day and hour pillars use "
               f"{'true solar time' if m.solar else 'local standard time'}; Zi hour: {ZI_RULES_EN[b.zi_rule]}.")
    return out


def _age_en(y: int, mo: int) -> str:
    return f"age {y}" + (f" and {mo} month{'s' if mo > 1 else ''}" if mo else "")


def _shensha_en(x: dict) -> dict:
    name = x["name"].replace("（桃花）", "")
    basis = re.fullmatch(r"(.)(干|支|柱)(.+?)(旬)?", x["basis"])
    p, side, chars, xun = basis.groups()
    if side == "柱":
        basis_en = f"the ten-day cycle of the {terms_en.PILLARS[p]} pillar {gz_en(chars)}"
    else:
        basis_en = f"{_pos(p, side)} {py(chars)}"
    return {**x, "label": _short(_BZ[name]), "basis": basis_en, "targets": _chars(x["targets"]),
            "hits": [f"{_pos(h[0], h[1])} {py(h[2])}" for h in x["hits"]]}


def _short(en: str) -> str:
    """页面上的短名：去掉术语表里的括注，如 'Void (empty branches of the decade)' → 'Void'。"""
    return en.split(" (")[0]


def _names() -> dict:
    """页面用到的中文键 → 英文显示名（数据键仍用中文，模板查这张表显示）。
    旺相休囚死的「死」与十二长生的「死」同字，前者用键「旺相:死」。"""
    n = {}
    n.update({k: v[0] for k, v in terms_en.SHISHEN.items()})
    n.update({k: v[0] for k, v in terms_en.CHANGSHENG.items()})
    n.update({f"旺相:{k}": _short(v) for k, v in terms_en.WANGXIANG.items()})
    n.update(terms_en.ELEMENTS)
    n.update({"阳": "Yang", "阴": "Yin"})
    n.update(terms_en.NAYIN)
    n.update(terms_en.QI)
    n.update(terms_en.PILLARS)
    for k in [*glossary.TERMS, "六合"]:
        n[k] = _short(_BZ[k])
    n["自刑"] = terms_en.XING_KINDS["自刑"]
    n["咸池（桃花）"] = n["咸池"]
    for ch in "甲乙丙丁戊己庚辛壬癸子丑寅卯辰巳午未申酉戌亥":
        n[ch] = py(ch)
    return n


def _term_pinyin() -> dict:
    """术语的拼音，英文页第一次出现时写成 Eating God (Shi Shen 食神)。"""
    out = {k: v[1] for k, v in terms_en.SHISHEN.items()}
    out.update({zh: p for zh, _, p in terms_en.BAZI})
    out.update({zh: p for zh, _, p in terms_en.COMMON})
    return out


def english(b: Bazi, d: dict) -> dict:
    """把 _bazi_data 的数据文字换成英文；排盘数据（干支、十神键、关系位置）不变。"""
    m = b.moment
    d = dict(d)
    natal = b.ganzhi
    d["lang"] = "en"
    d["title"] = bazi_title(b, "en")
    d["gender"] = "Male" if b.gender == "m" else "Female"
    facts = [("Born", f"{m.clock:%Y-%m-%d}" + (f" {m.clock:%H:%M}" if m.time_known else " (time unknown)")),
             ("Lunar date", lunar_en(b.lunar)), ("Time zone", m.tz)]
    if m.solar is not None:
        facts.append(("True solar time", f"{m.solar:%H:%M} (longitude {m.longitude}°)"))
    if m.time_known:
        facts.append(("Zi hour", "day changes at 23:00" if b.zi_rule == "next" else "late Zi keeps the day"))
    y, mo, dd = b.qiyun
    facts.append(("Luck Pillars start", f"{y} y {mo} m {dd} d after birth ({b.qiyun_date:%Y-%m-%d})"))
    g = b.mingua
    facts.append(("Kua", f"{py(g.gua)} · {'East' if g.group.startswith('东') else 'West'} Group"))
    d["facts"] = facts
    d["warnings"] = [_warning_en(w) for w in b.warnings]
    d["time_lines"] = _time_lines_en(b)
    for kind in ("gan", "zhi"):
        rels = []
        for r, raw in zip(d["relations"][kind], b.relations[kind]):
            label, short = relation_label_en(raw)
            rels.append({**r, "label": label, "short": short})
        d["relations"] = {**d["relations"], kind: rels}
    d["dayun"] = [{**x, "age": _age_en(*dy.start_age), "age_short": f"age {dy.start_age[0]}",
                   "relations": against_natal_en(dy.ganzhi, natal, "Luck Pillar"),
                   "years": [{**yr, "relations": against_natal_en(yr["gz"], natal, "Year")} for yr in x["years"]]}
                  for x, dy in zip(d["dayun"], b.dayun)]
    d["pre_years"] = [{**yr, "relations": against_natal_en(yr["gz"], natal, "Year")} for yr in d["pre_years"]]
    d["wangxiang"] = {**d["wangxiang"], "season_en": terms_en.SEASONS[d["wangxiang"]["season"]]}
    sl = d["siling"]
    d["siling"] = {**sl, "jie_en": terms_en.JIEQI[sl["jie"]], "ruler_en": f"{py(sl['ruler'][0])} {wx_en(sl['ruler'][1])}",
                   "table": [{**t, "name_en": f"{py(t['name'][0])} {wx_en(t['name'][1])}"} for t in sl["table"]]}
    d["shensha"] = [_shensha_en(x) for x in d["shensha"]]
    d["tiaohou"] = {**d["tiaohou"], "kind_en": {"专论": "This month", "合论": "Shared", "季论": "Season"}}
    d["glossary"] = glossary.page_data("en")
    d["names"] = _names()
    d["term_py"] = {**_term_pinyin(), **{k: _CS_PY[k] for k in terms_en.CHANGSHENG}}
    d["source"] = (f"bazi-mingli · kanyu v{__version__} · generated {_dt.date.today():%Y-%m-%d} · chart and tables "
                   "computed by scripts/bazi.py; notes are interpretation, not computed results")
    return d
