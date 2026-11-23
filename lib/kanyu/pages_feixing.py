"""飞星盘页面数据（fengshui-master）。模板 assets/templates/feixing.html。

lang="zh" 或 "en"：页面上的数据文字在这里按语言生成，界面文字在模板的字典里；
英文术语一律取自 terms_en.py。
"""

from __future__ import annotations

import datetime as _dt
import json

from . import __version__, terms_en
from .core import (GRID, LUOSHU_PATH, MOUNTAINS, PALACE_DIR, PALACES, STAR_NAMES,
                   deg_to_mountain, fly, mountain_center_deg, mountain_palace, mountain_yinyang, neighbor)
from .feixing import Chart, jian_warnings, main_pattern, palace_flags, star_status

LANGS = ("zh", "en")

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
# 英文页面：原文后附我们的译文（our translation）
GUA_XIANG_EN = {
    "乾": "Qian is heaven, a circle, the ruler, the father, jade, metal",
    "坤": "Kun is earth, the mother, cloth, a cauldron, evenness, the multitude",
    "震": "Zhen is thunder, the dragon, the eldest son, a great highway, decisive haste",
    "巽": "Xun is wood, wind, the eldest daughter, a plumb line, the craftsman, height",
    "坎": "Kan is water, ditches and channels, what lies hidden, the middle son",
    "离": "Li is fire, the sun, lightning, the middle daughter, armour and helmets",
    "艮": "Gen is the mountain, a footpath, small stones, gateways, the youngest son",
    "兑": "Dui is the marsh, the youngest daughter, the sorceress, mouth and tongue, breaking and ruin",
}
GUA_DEG = {"坎": 0, "艮": 45, "震": 90, "巽": 135, "离": 180, "坤": 225, "兑": 270, "乾": 315}

# 星曜旺衰在页面上的着色
GOOD = {"当令旺星", "生气（下运旺）", "次生气"}
BAD = {"五黄煞", "死气", "衰气"}

# 格局的英文：(名称, 说明)。键与 feixing.chart_patterns 的输出一一对应（tests/test_pages.py 检查）。
_FS = {zh: en for zh, en, _ in terms_en.FENGSHUI}
PATTERN_EN = {
    "旺山旺向（当令山星到坐、向星到向）":
        (_FS["旺山旺向"], "the timely Mountain Star reaches the sitting palace and the timely Facing Star the facing palace"),
    "上山下水（当令山星到向、向星到坐）":
        (_FS["上山下水"], "the timely Mountain Star falls at the facing and the timely Facing Star at the sitting"),
    "双星到向（当令山向二星同到向首）": (_FS["双星到向"], "both timely stars meet at the facing palace"),
    "双星到坐（当令山向二星同到坐山）": (_FS["双星到坐"], "both timely stars meet at the sitting palace"),
    "山星伏吟（五入中顺飞，与洛书元旦盘相同）":
        ("Mountain Stars Repeating (Fu Yin)", "5 enters the center and flies forward, matching the Lo Shu"),
    "山星反吟（五入中逆飞，与洛书元旦盘相反）":
        ("Mountain Stars Opposing (Fan Yin)", "5 enters the center and flies backward, reversing the Lo Shu"),
    "向星伏吟（五入中顺飞，与洛书元旦盘相同）":
        ("Facing Stars Repeating (Fu Yin)", "5 enters the center and flies forward, matching the Lo Shu"),
    "向星反吟（五入中逆飞，与洛书元旦盘相反）":
        ("Facing Stars Opposing (Fan Yin)", "5 enters the center and flies backward, reversing the Lo Shu"),
    "山星与运星合十": ("Mountain and Period Stars Combine to Ten", "they add up to 10 in every palace"),
    "向星与运星合十": ("Facing and Period Stars Combine to Ten", "they add up to 10 in every palace"),
    "父母三般卦（每宫运山向三星成 147/258/369）":
        (_FS["父母三般卦"].split(" (")[0], "in every palace the period, mountain and facing stars form 1-4-7, 2-5-8 or 3-6-9"),
    "连珠三般卦（每宫运山向三星相连）":
        (_FS["连珠三般卦"], "in every palace the three stars are consecutive numbers"),
}
STATUS_EN = {   # 页面上的短说法；完整译名见 terms_en.FENGSHUI
    "当令旺星": "timely", "生气（下运旺）": "growing",
    "次生气": "secondary growing", "退气": "retreating", "五黄煞": "5 Yellow affliction",
    "衰气": "declining", "死气": "dormant",
}
FLAG_EN = {"五黄": _FS["五黄"], "二五交加": _FS["二五交加"]}

NOTES_KEYS = {"summary", "palaces", "advice"}
NUM_CN = ["", "一", "二", "三", "四", "五", "六", "七", "八", "九"]


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


# --- 英文文字 ------------------------------------------------------------------------

def mountain_code(m: str) -> str:
    """英文飞星书常用的山向代号：方位 + 宫内序号，如 子 = N2、丑 = NE1。"""
    # MOUNTAINS 自壬起，每宫三山依次排列，故宫内序号 = 下标 % 3 + 1
    return f"{terms_en.DIR_ABBR[PALACE_DIR[mountain_palace(m)]]}{MOUNTAINS.index(m) % 3 + 1}"


def mountain_en(m: str) -> str:
    return f"{terms_en.pinyin(m)} ({mountain_code(m)})"


def _yy_en(m: str) -> str:
    return "yang" if mountain_yinyang(m) == "+" else "yin"


def pattern_text(p: str, lang: str) -> str:
    if lang == "zh":
        return p
    name, why = PATTERN_EN[p]
    return f"{name} ({why})"


def status_text(st: str, yun: int, lang: str) -> str:
    if lang == "zh":
        return f"{NUM_CN[yun]}运{st.replace('（下运旺）', '')}"
    return f"{STATUS_EN[st]} in Period {yun}"


def star_name(n: int, lang: str) -> str:
    if lang == "zh":
        return STAR_NAMES[n]
    color, name, _ = terms_en.STARS[n]
    return f"{color} ({name})"


def star_short(n: int, lang: str) -> str:
    return STAR_NAMES[n][2:] if lang == "zh" else terms_en.STARS[n][1]


def _warnings_en(sit: str, off: float) -> list[str]:
    w = []
    a = abs(off)
    if a >= 6:
        nb = neighbor(sit, 1 if off > 0 else -1)
        kind = ("minor void: same palace, different dragon sector" if mountain_palace(nb) == mountain_palace(sit)
                else "major void: crosses into another trigram")
        w.append(f"Close to the {terms_en.pinyin(sit)}/{terms_en.pinyin(nb)} boundary ({kind}). "
                 "The facing is unclear; measure again.")
    if a > 3:
        w.append("The facing is more than 3° off the centre line. Most Flying Star schools use the Replacement Chart here; "
                 "schools differ on the exact threshold, so read both charts.")
    return w


# --- 页面数据 ------------------------------------------------------------------------

def feixing_data(ch: Chart, *, annual: int | None, annual_label: str | None, month: int | None,
                 facing_deg: float | None, yun_note: str, current_yun: int, notes: dict,
                 lang: str = "zh") -> dict:
    if lang not in LANGS:
        raise ValueError(f"lang 应为 {'/'.join(LANGS)}")
    en = lang == "en"
    ann = fly(annual) if annual else None
    mon = fly(month) if month else None
    palaces = {}
    for p in LUOSHU_PATH:
        flags = palace_flags(ch.shan[p], ch.xiang[p], ann[p] if ann else None)
        if en:
            label = "Center" if p == "中" else f"{terms_en.pinyin(p)} · {terms_en.DIR_ABBR[PALACE_DIR[p]]}"
            name = "Center Palace" if p == "中" else f"{terms_en.pinyin(p)} Palace · {terms_en.DIRECTIONS[PALACE_DIR[p]]}"
            xiang = f"{GUA_XIANG[p]} — {GUA_XIANG_EN[p]}" if p in GUA_XIANG else ""
        else:
            label = p + ("" if p == "中" else f" · {PALACE_DIR[p]}")
            name = "中宫" if p == "中" else f"{p}宫 · {PALACE_DIR[p]}"
            xiang = GUA_XIANG.get(p, "")
        palaces[p] = {"dir": PALACE_DIR[p], "label": label, "name": name, "xiang": xiang,
                      "flags": [FLAG_EN[f] if en else f for f in flags]}

    tigua = ("Replacement Chart" if ch.tigua else "Standard Chart") if en else ("替卦" if ch.tigua else "下卦")
    if en:
        facts = [("Period", str(ch.yun)),
                 ("Orientation", f"sitting {mountain_en(ch.sit)}, facing {mountain_en(ch.facing)}"),
                 ("Chart", tigua)]
    else:
        facts = [("元运", f"{NUM_CN[ch.yun]}运"), ("坐向", f"坐{ch.sit}向{ch.facing}"), ("排法", tigua)]
    warnings = []
    axis = facing_deg if facing_deg is not None else mountain_center_deg(ch.facing)
    if facing_deg is not None:
        _, off = deg_to_mountain((facing_deg + 180) % 360)
        if en:
            facts.append(("Compass", f"facing {facing_deg:.1f}° ({off:+.1f}° from the {terms_en.pinyin(ch.sit)} centre line)"))
            warnings = _warnings_en(ch.sit, off)
        else:
            facts.append(("罗盘", f"向 {facing_deg:.1f}°（偏{ch.sit}山中线 {off:+.1f}°）"))
            warnings = [w.lstrip("⚠ ").replace("（--tigua）", "") for w in jian_warnings(ch.sit, off)]
    if annual:
        facts.append(("Annual", f"{annual_label + ' · ' if annual_label else ''}star {annual} at the center") if en
                     else ("流年", f"{annual_label or ''}{NUM_CN[annual]}入中".strip()))
    if month:
        facts.append(("Monthly", f"star {month} at the center") if en else ("流月", f"{NUM_CN[month]}入中"))

    entries = []
    for key, e in (("山星", ch.shan_entry), ("向星", ch.xiang_entry)):
        if en:
            label = "Mountain Star" if key == "山星" else "Facing Star"
            why = (f"by the {terms_en.pinyin(e.by)} mountain ({_yy_en(e.by)})" if e.n != 5
                   else f"5 at the center follows the {terms_en.pinyin(e.by)} mountain itself ({_yy_en(e.by)})")
            line = (f"{label}: period star {e.n} enters the center; {why}, it flies "
                    f"{'forward' if e.forward else 'backward'}")
            if e.replaced:
                line += f"; the Replacement Chart uses {e.center} instead"
        else:
            why = f"依{e.by}山（{mountain_yinyang(e.by)}）" if e.n != 5 else f"五入中依{e.by}山本身（{mountain_yinyang(e.by)}）"
            line = f"{key}：运盘{NUM_CN[e.n]}入中，{why}{'顺' if e.forward else '逆'}飞"
            if e.replaced:
                line += f"，替卦以{NUM_CN[e.center]}代之"
        entries.append(line)

    mountains = [{"name": m, "label": terms_en.pinyin(m) if en else m,
                  "deg": mountain_center_deg(m), "boundary": i % 3 == 0}
                 for i, m in enumerate(MOUNTAINS)]
    status = {n: star_status(n, current_yun) for n in range(1, 10)}
    chart_status = {n: star_status(n, ch.yun) for n in range(1, 10)} if ch.yun != current_yun else None
    if en:
        title = f"Period {ch.yun} · Sitting {terms_en.pinyin(ch.sit)}, Facing {terms_en.pinyin(ch.facing)}"
        source = (f"Kanyuzi fengshui-master v{__version__} · generated {_dt.date.today():%Y-%m-%d} · "
                  f"chart computed by scripts/fengshui.py; star strength read for the current Period {current_yun}")
    else:
        title = f"{NUM_CN[ch.yun]}运 · {ch.sit}山{ch.facing}向"
        source = (f"堪舆子 fengshui-master v{__version__} · 生成于 {_dt.date.today():%Y-%m-%d} · "
                  f"盘面由 scripts/fengshui.py 计算，旺衰按当前{NUM_CN[current_yun]}运论")
    pats = ch.patterns
    return {
        "lang": lang,
        "title": title,
        "facts": facts, "warnings": warnings, "yun_note": yun_note,
        "sit": ch.sit, "facing": ch.facing, "sit_palace": ch.sit_palace, "face_palace": ch.face_palace,
        "axis_deg": axis,
        "patterns": [pattern_text(p, lang) for p in pats], "main_pattern": main_pattern(ch),
        "entries": entries,
        "layers": {"yun": ch.yunpan, "shan": ch.shan, "xiang": ch.xiang, "annual": ann, "month": mon},
        "current_yun": current_yun,
        "nums": [str(i) for i in range(10)] if en else NUM_CN,
        "status": status, "chart_status": chart_status,
        "status_class": {n: "good" if s in GOOD else ("bad" if s in BAD else "") for n, s in status.items()},
        "status_text": {n: status_text(s, current_yun, lang) for n, s in status.items()},
        "status_short": {n: (STATUS_EN[s] if en else s.replace("（下运旺）", ""))
                         for n, s in status.items()},
        # 本盘元运与当前元运不同时，列出旺衰也不同的星（批注里注明「本盘当时为……」）
        "chart_status_text": ({n: status_text(s, ch.yun, lang) for n, s in chart_status.items() if s != status[n]}
                              if chart_status else None),
        "star_names": {n: star_name(n, lang) for n in range(1, 10)},
        "star_short": {n: star_short(n, lang) for n in range(1, 10)},
        "palaces": palaces, "grid": GRID, "path": LUOSHU_PATH,
        "mountains": mountains,
        "gua_ring": [{"name": g, "label": terms_en.pinyin(g) if en else g, "deg": GUA_DEG[g]} for g in PALACES],
        "notes": notes,
        "autoplay": True,
        "source": source,
    }


def yun_note(year_text: str, yun: int, start: int, end: int, lang: str = "zh") -> str:
    if lang == "en":
        return (f"Period: {year_text} → Period {yun} ({start}–{end}, divided at the Start of Spring). "
                "The chart is set by the move-in or major-renovation date.")
    return f"元运：{year_text} → {yun}运（{start}-{end}，以立春为界）。以入住或大修完工时间立极。"


def page_title(ch: Chart, lang: str = "zh") -> str:
    if lang == "en":
        return f"Flying Star Chart · Sitting {terms_en.pinyin(ch.sit)}, Facing {terms_en.pinyin(ch.facing)}"
    return f"飞星盘 {ch.sit}山{ch.facing}向"


def default_name(ch: Chart, lang: str = "zh") -> str:
    if lang == "en":
        return f"flying-stars-period{ch.yun}-{terms_en.pinyin(ch.sit)}-{terms_en.pinyin(ch.facing)}.html".lower()
    return f"飞星盘-{ch.yun}运-{ch.sit}山{ch.facing}向.html"
