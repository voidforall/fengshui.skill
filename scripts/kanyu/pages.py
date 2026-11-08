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
from .core import (GRID, LUOSHU_PATH, MOUNTAINS, PALACE_DIR, PALACES, STAR_NAMES,
                   deg_to_mountain, fly, mountain_center_deg, mountain_yinyang)
from .bazhai import YOUNIAN_JI, YOUNIAN_NOTE
from .feixing import Chart, jian_warnings, main_pattern, palace_flags, star_status
from .layout import Member, house_gua, palace_younian

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

NOTES_KEYS = {"summary", "palaces", "rooms", "advice"}


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
        raise ValueError(f"notes 含未知字段：{'、'.join(sorted(unknown))}（可用：summary、palaces、rooms、advice）")
    pals = notes.get("palaces", {})
    bad = set(pals) - set(PALACE_DIR)
    if bad:
        raise ValueError(f"notes.palaces 的键应为宫名（坎坤震巽中乾兑艮离），收到：{'、'.join(sorted(bad))}")
    rooms = notes.get("rooms", {})
    if not isinstance(rooms, dict) or not all(isinstance(v, str) for v in rooms.values()):
        raise ValueError("notes.rooms 应为 {房间名: 文字}")
    if not all(isinstance(v, str) for v in pals.values()) or not isinstance(notes.get("summary", ""), str) \
            or not all(isinstance(a, str) for a in notes.get("advice", [])):
        raise ValueError("notes 中的批注应为文字")
    return notes


def _embed_json(data) -> str:
    # 防止批注文字中的 </script> 截断脚本
    return json.dumps(data, ensure_ascii=False).replace("</", "<\\/")


def _escape_html(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# 签筒里备用的常见房间（未在 --rooms 中给出的，作为空签供用户自己摆放）
SPARE_ROOMS = ["大门", "客厅", "主卧", "次卧", "书房", "厨房", "卫生间", "儿童房", "老人房"]


def feixing_data(ch: Chart, *, annual: int | None, annual_label: str | None, month: int | None,
                 facing_deg: float | None, yun_note: str, current_yun: int, notes: dict,
                 rooms: list[tuple[str, str]] | None = None, members: list[Member] | None = None) -> dict:
    ann = fly(annual) if annual else None
    mon = fly(month) if month else None
    palaces = {}
    for p in LUOSHU_PATH:
        palaces[p] = {
            "dir": PALACE_DIR[p],
            "xiang": GUA_XIANG.get(p, ""),
            "flags": palace_flags(ch.shan[p], ch.xiang[p], ann[p] if ann else None),
        }
    facts = [("坐向", f"坐{ch.sit}向{ch.facing}"),
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
    rooms = rooms or []
    members = members or []
    hg, hgroup = house_gua(ch)
    given = {name for name, _ in rooms}
    room_cards = [{"name": n, "palace": p} for n, p in rooms] + \
                 [{"name": n, "palace": None} for n in SPARE_ROOMS if n not in given]
    return {
        "title": f"{ch.sit}山{ch.facing}向",
        "subtitle": f"{NUM_CN[ch.yun]}运宅",
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
        "rooms": room_cards,
        "house": {"label": "宅", "gua": hg, "group": hgroup, "younian": palace_younian(hg)},
        "members": [{"label": m.label, "gua": m.mingua.gua, "number": m.mingua.number,
                     "group": m.mingua.group, "younian": m.younian} for m in members],
        "younian_ji": sorted(YOUNIAN_JI), "younian_note": YOUNIAN_NOTE,
        "autoplay": True,
        "source": f"由堪舆子 fengshui-master v{__version__} 于 {_dt.date.today():%Y-%m-%d} 生成。"
                  f"盘面由 scripts/fengshui.py 计算，旺衰按当前{NUM_CN[current_yun]}运论。",
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

