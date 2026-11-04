#!/usr/bin/env python3
"""堪舆确定性计算工具 —— 供 fengshui-master skill 调用。

所有「可计算」的部分（排盘、查表、历法）都在这里完成，模型只负责解读。

子命令:
  mingua   命卦（八宅）
  bazhai   八宅游年：宅卦 / 命卦 的四吉四凶方
  feixing  玄空飞星排盘（下卦 / 替卦，可叠加流年、流月）
  liunian  流年 / 流月紫白飞星
  day      某日历法信息：四柱、节气、建除、黄黑道、神煞、宜忌
  zeri     在日期范围内按事项筛选择日候选
  bazi     八字四柱、五行、十神、大运

飞星 / 八宅 / 命卦只依赖标准库；历法相关命令（day / zeri / bazi，
以及按立春精确分年）需要 `pip install lunar_python`。
"""

from __future__ import annotations

import argparse
import datetime as _dt
import math
import sys

try:  # 历法库为可选依赖
    from lunar_python import Lunar, Solar  # type: ignore

    HAS_LUNAR = True
except ImportError:  # pragma: no cover - 取决于环境
    HAS_LUNAR = False


# ---------------------------------------------------------------------------
# 基础常量
# ---------------------------------------------------------------------------

GAN = "甲乙丙丁戊己庚辛壬癸"
ZHI = "子丑寅卯辰巳午未申酉戌亥"
SHENGXIAO = "鼠牛虎兔龙蛇马羊猴鸡狗猪"

# 二十四山，自壬起顺时针；第 i 山的中心度数 = (345 + 15*i) % 360
MOUNTAINS = "壬子癸丑艮寅甲卯乙辰巽巳丙午丁未坤申庚酉辛戌乾亥"
# 每 3 山一宫
PALACES = ["坎", "艮", "震", "巽", "离", "坤", "兑", "乾"]
PALACE_NUM = {"坎": 1, "坤": 2, "震": 3, "巽": 4, "中": 5, "乾": 6, "兑": 7, "艮": 8, "离": 9}
NUM_PALACE = {v: k for k, v in PALACE_NUM.items()}
PALACE_DIR = {
    "坎": "北", "艮": "东北", "震": "东", "巽": "东南",
    "离": "南", "坤": "西南", "兑": "西", "乾": "西北", "中": "中",
}
DIR_PALACE = {v: k for k, v in PALACE_DIR.items()}
YUANLONG = ["地元", "天元", "人元"]  # 每宫三山依次为 地 / 天 / 人 元龙

STAR_NAMES = {
    1: "一白贪狼", 2: "二黑巨门", 3: "三碧禄存", 4: "四绿文曲", 5: "五黄廉贞",
    6: "六白武曲", 7: "七赤破军", 8: "八白左辅", 9: "九紫右弼",
}

# 洛书飞泊路径：中→乾→兑→艮→离→坎→坤→震→巽
LUOSHU_PATH = ["中", "乾", "兑", "艮", "离", "坎", "坤", "震", "巽"]

# 九宫格显示布局（上南下北，传统罗盘图式）
GRID = [["巽", "离", "坤"], ["震", "中", "兑"], ["艮", "坎", "乾"]]

# 替卦（《沈氏玄空学》替卦诀）：
#   子癸甲申贪狼一路行；坤壬乙卯未巨门从头出；
#   戌乾亥辰巽巳武曲位；艮丙辛酉丑破军；寅午庚丁右弼。
TIGUA_STAR = {}
for _ms, _n in [("子癸甲申", 1), ("坤壬乙卯未", 2), ("戌乾亥辰巽巳", 6),
                ("艮丙辛酉丑", 7), ("寅午庚丁", 9)]:
    for _m in _ms:
        TIGUA_STAR[_m] = _n
assert len(TIGUA_STAR) == 24


def mountain_index(m: str) -> int:
    i = MOUNTAINS.find(m)
    if i < 0 or len(m) != 1:
        raise ValueError(f"未知山名: {m!r}（应为二十四山之一: {MOUNTAINS}）")
    return i


def mountain_palace(m: str) -> str:
    return PALACES[mountain_index(m) // 3]


def mountain_yuanlong(m: str) -> int:
    return mountain_index(m) % 3


def mountain_yinyang(m: str) -> str:
    """玄空二十四山阴阳（不同于八字地支阴阳）。

    一三七九（坎震兑离）四正宫：地元阳、天元阴、人元阴；
    二四六八（坤巽乾艮）四隅宫：地元阴、天元阳、人元阳。
    """
    pal = mountain_palace(m)
    yl = mountain_yuanlong(m)
    if PALACE_NUM[pal] % 2 == 1:
        return "+" if yl == 0 else "-"
    return "-" if yl == 0 else "+"


def opposite(m: str) -> str:
    return MOUNTAINS[(mountain_index(m) + 12) % 24]


def mountain_center_deg(m: str) -> float:
    return (345 + 15 * mountain_index(m)) % 360


def deg_to_mountain(deg: float) -> tuple[str, float]:
    """度数 → (所在山, 偏离该山中线的度数，正为顺时针偏)。"""
    deg = deg % 360
    i = int(((deg - 337.5) % 360) // 15)
    m = MOUNTAINS[i]
    off = (deg - mountain_center_deg(m) + 180) % 360 - 180
    return m, off


def parse_direction(s: str) -> tuple[str, float | None]:
    """接受山名（如「子」）或度数（如「182.5」）。返回 (山, 度数或 None)。"""
    s = s.strip().rstrip("°度")
    if len(s) == 1 and s in MOUNTAINS:
        return s, None
    try:
        deg = float(s)
    except ValueError:
        raise ValueError(f"无法识别方向 {s!r}：请给二十四山名或罗盘度数") from None
    return deg_to_mountain(deg)[0], deg % 360


def fly(center: int, forward: bool) -> dict[str, int]:
    """从中宫起 center 星，沿洛书路径顺飞(forward)或逆飞。"""
    out = {}
    for k, pal in enumerate(LUOSHU_PATH):
        step = k if forward else -k
        out[pal] = (center - 1 + step) % 9 + 1
    return out


# ---------------------------------------------------------------------------
# 元运 / 年份
# ---------------------------------------------------------------------------

def yun_of_year(year: int) -> int:
    """三元九运：1864 年起一运，每运 20 年（年份以立春为界）。"""
    return (year - 1864) // 20 % 9 + 1


def yun_range(yun: int) -> tuple[int, int]:
    start = 1864 + (yun - 1) * 20
    return start, start + 19


def lichun_year(d: _dt.date | _dt.datetime) -> tuple[int, bool]:
    """返回以立春为界的年份，以及是否精确（False 表示按 2 月 4 日近似）。"""
    if HAS_LUNAR:
        if isinstance(d, _dt.datetime):
            sol = Solar.fromYmdHms(d.year, d.month, d.day, d.hour, d.minute, d.second)
        else:
            sol = Solar.fromYmdHms(d.year, d.month, d.day, 12, 0, 0)
        gz = sol.getLunar().getYearInGanZhiByLiChun()
        # 由干支反推年份（离公历年至多差 1）
        for y in (d.year, d.year - 1):
            if ganzhi_of_year(y) == gz:
                return y, True
    approx = d.year if (d.month, d.day) >= (2, 4) else d.year - 1
    return approx, False


def ganzhi_of_year(year: int) -> str:
    return GAN[(year - 4) % 10] + ZHI[(year - 4) % 12]


def parse_date(s: str) -> _dt.datetime:
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M", "%Y-%m-%d", "%Y/%m/%d", "%Y%m%d"):
        try:
            return _dt.datetime.strptime(s.strip(), fmt)
        except ValueError:
            pass
    if s.strip().isdigit() and len(s.strip()) == 4:
        return _dt.datetime(int(s), 6, 1)
    raise ValueError(f"无法解析日期 {s!r}（格式 YYYY-MM-DD 或 'YYYY-MM-DD HH:MM'）")


# ---------------------------------------------------------------------------
# 八宅：命卦与游年
# ---------------------------------------------------------------------------

BAZHAI_ORDER = ["乾", "坎", "艮", "震", "巽", "离", "坤", "兑"]
# 游年歌诀（《八宅明镜》）：自本卦之后依 坎艮震巽离坤兑乾 顺序读出
YOUNIAN_SONG = {
    "乾": "六天五祸绝延生", "坎": "五天生延绝祸六", "艮": "六绝祸生延天五",
    "震": "延生祸绝五天六", "巽": "天五六祸生绝延", "离": "六五绝延祸生天",
    "坤": "天延绝生祸五六", "兑": "生祸延绝六五天",
}
YOUNIAN_NAMES = {"生": "生气", "延": "延年", "天": "天医", "祸": "祸害",
                 "六": "六煞", "五": "五鬼", "绝": "绝命"}
YOUNIAN_ORDER = ["生气", "延年", "天医", "伏位", "祸害", "六煞", "五鬼", "绝命"]
YOUNIAN_JI = {"生气", "延年", "天医", "伏位"}
YOUNIAN_NOTE = {
    "生气": "上吉（贪狼木）", "延年": "上吉（武曲金）", "天医": "中吉（巨门土）",
    "伏位": "小吉（辅弼木）", "祸害": "小凶（禄存土）", "六煞": "次凶（文曲水）",
    "五鬼": "大凶（廉贞火）", "绝命": "大凶（破军金）",
}
EAST_FOUR = {"坎", "离", "震", "巽"}


def younian(gua: str) -> dict[str, str]:
    """返回 {游年名: 方位卦}。"""
    i = BAZHAI_ORDER.index(gua)
    others = [BAZHAI_ORDER[(i + k) % 8] for k in range(1, 8)]
    table = {"伏位": gua}
    for t, c in zip(others, YOUNIAN_SONG[gua]):
        table[YOUNIAN_NAMES[c]] = t
    return table


def mingua(year: int, gender: str) -> int:
    """命卦数（年份须已按立春调整）。男命五寄坤(2)，女命五寄艮(8)。"""
    g = gender.lower()
    if g in ("m", "male", "男", "男命"):
        n = (11 - year % 9) % 9 or 9
        return 2 if n == 5 else n
    if g in ("f", "female", "女", "女命"):
        n = (year % 9 + 4) % 9 or 9
        return 8 if n == 5 else n
    raise ValueError("gender 应为 m/f 或 男/女")


def east_west(gua: str) -> str:
    return "东四" if gua in EAST_FOUR else "西四"


# ---------------------------------------------------------------------------
# 玄空飞星
# ---------------------------------------------------------------------------

def _star_direction(n: int, ref_mountain: str) -> tuple[bool, str]:
    """入中之星 n 的顺逆：取 n 原宫中与 ref_mountain 同元龙之山的阴阳。

    n == 5 无宫可归，以 ref_mountain（坐山或向首）本身阴阳论。
    返回 (是否顺飞, 用以定阴阳的山)。
    """
    if n == 5:
        m = ref_mountain
    else:
        pal = NUM_PALACE[n]
        m = MOUNTAINS[PALACES.index(pal) * 3 + mountain_yuanlong(ref_mountain)]
    return mountain_yinyang(m) == "+", m


def star_status(n: int, yun: int) -> str:
    """以元运论星之旺衰（各派细分略有出入，此为常用口径）。"""
    if n == yun:
        return "当令旺星"
    d = (n - yun) % 9
    if d == 1:
        return "生气（下运旺）"
    if d == 2:
        return "次生气"
    if d == 8:
        return "退气"
    if n == 5:
        return "五黄煞"
    if d == 7:
        return "衰气"
    return "死气"


def feixing_chart(yun: int, sit: str, tigua: bool = False) -> dict:
    facing = opposite(sit)
    sit_pal, face_pal = mountain_palace(sit), mountain_palace(facing)
    yunpan = fly(yun, True)

    def build(ref: str, pal: str):
        n = yunpan[pal]
        forward, by = _star_direction(n, ref)
        center = n
        replaced = None
        if tigua and n != 5:
            center = TIGUA_STAR[by]
            replaced = (n, center, by)
        return fly(center, forward), forward, n, by, replaced

    shan, shan_fwd, shan_n, shan_by, shan_rep = build(sit, sit_pal)
    xiang, xiang_fwd, xiang_n, xiang_by, xiang_rep = build(facing, face_pal)

    return {
        "yun": yun, "sit": sit, "facing": facing,
        "sit_palace": sit_pal, "face_palace": face_pal,
        "tigua": tigua,
        "yunpan": yunpan, "shan": shan, "xiang": xiang,
        "shan_info": (shan_n, shan_by, shan_fwd, shan_rep),
        "xiang_info": (xiang_n, xiang_by, xiang_fwd, xiang_rep),
        "patterns": chart_patterns(yun, sit_pal, face_pal, yunpan, shan, xiang,
                                   shan["中"], xiang["中"], shan_fwd, xiang_fwd),
    }


def chart_patterns(yun, sit_pal, face_pal, yunpan, shan, xiang,
                   shan_c, xiang_c, shan_fwd, xiang_fwd) -> list[str]:
    pats = []
    s_sit, s_face = shan[sit_pal], shan[face_pal]
    x_sit, x_face = xiang[sit_pal], xiang[face_pal]
    if s_sit == yun and x_face == yun:
        pats.append("旺山旺向（当令山星到坐、向星到向）")
    elif s_face == yun and x_sit == yun:
        pats.append("上山下水（当令山星到向、向星到坐）")
    elif s_face == yun and x_face == yun:
        pats.append("双星到向（当令山向二星同到向首）")
    elif s_sit == yun and x_sit == yun:
        pats.append("双星到坐（当令山向二星同到坐山）")

    for name, c, fwd in (("山星", shan_c, shan_fwd), ("向星", xiang_c, xiang_fwd)):
        if c == 5:
            pats.append(f"{name}伏吟（五入中顺飞，与洛书元旦盘相同）" if fwd
                        else f"{name}反吟（五入中逆飞，与洛书元旦盘相反）")

    if all(shan[p] + yunpan[p] == 10 for p in LUOSHU_PATH):
        pats.append("山星与运星合十")
    if all(xiang[p] + yunpan[p] == 10 for p in LUOSHU_PATH):
        pats.append("向星与运星合十")
    groups = [{1, 4, 7}, {2, 5, 8}, {3, 6, 9}]
    if all({yunpan[p], shan[p], xiang[p]} in groups for p in LUOSHU_PATH):
        pats.append("父母三般卦（每宫运山向三星成 147/258/369）")

    def consecutive(t):
        return any({(a + k - 1) % 9 + 1 for k in range(3)} == set(t) for a in range(1, 10))
    if all(consecutive((yunpan[p], shan[p], xiang[p])) for p in LUOSHU_PATH):
        pats.append("连珠三般卦（每宫运山向三星相连）")
    return pats


# ---------------------------------------------------------------------------
# 流年 / 流月紫白
# ---------------------------------------------------------------------------

def annual_center(year: int) -> int:
    """流年中宫星（年份以立春为界）。如 2024=三碧、2025=二黑、2026=一白。"""
    return (10 - year % 9) % 9 + 1


def monthly_center(year: int, month_index: int) -> int:
    """流月中宫星。month_index: 寅月=1 … 丑月=12（节气月）。

    子午卯酉年寅月起八白，辰戌丑未年起五黄，寅申巳亥年起二黑，逐月逆减。
    """
    zhi = ZHI[(year - 4) % 12]
    start = {**dict.fromkeys("子午卯酉", 8), **dict.fromkeys("辰戌丑未", 5),
             **dict.fromkeys("寅申巳亥", 2)}[zhi]
    return (start - 1 - (month_index - 1)) % 9 + 1


def palace_of_star(chart: dict[str, int], n: int) -> str:
    return next(p for p, v in chart.items() if v == n)


# 年家煞方
SANSHA = {  # 三煞方（以年支三合局论）
    **dict.fromkeys("申子辰", ("南", "巳午未")),
    **dict.fromkeys("寅午戌", ("北", "亥子丑")),
    **dict.fromkeys("亥卯未", ("西", "申酉戌")),
    **dict.fromkeys("巳酉丑", ("东", "寅卯辰")),
}
ZHI_DIR = {"子": "北", "丑": "东北", "寅": "东北", "卯": "东", "辰": "东南", "巳": "东南",
           "午": "南", "未": "西南", "申": "西南", "酉": "西", "戌": "西北", "亥": "西北"}


def year_sha(year: int) -> dict:
    zhi = ZHI[(year - 4) % 12]
    chong = ZHI[(ZHI.index(zhi) + 6) % 12]
    ann = fly(annual_center(year), True)
    return {
        "ganzhi": ganzhi_of_year(year),
        "taisui": f"{ZHI_DIR[zhi]}（{zhi}山）",
        "suipo": f"{ZHI_DIR[chong]}（{chong}山）",
        "sansha": f"{SANSHA[zhi][0]}（{SANSHA[zhi][1]}）",
        "wuhuang": PALACE_DIR[palace_of_star(ann, 5)],
        "erhei": PALACE_DIR[palace_of_star(ann, 2)],
        "center": annual_center(year),
    }


# ---------------------------------------------------------------------------
# 文字输出
# ---------------------------------------------------------------------------

def render_grid(cell, width: int = 14) -> str:
    """cell(palace) -> list[str]；按上南下北布局输出九宫格。"""
    lines = []
    sep = "+" + ("-" * width + "+") * 3
    lines.append(sep)
    for row in GRID:
        cells = [cell(p) for p in row]
        h = max(len(c) for c in cells)
        for i in range(h):
            parts = []
            for c in cells:
                t = c[i] if i < len(c) else ""
                pad = width - _display_width(t)
                parts.append(" " + t + " " * max(pad - 1, 0))
            lines.append("|" + "|".join(parts) + "|")
        lines.append(sep)
    return "\n".join(lines)


def _display_width(s: str) -> int:
    return sum(2 if ord(ch) > 0x2E80 else 1 for ch in s)


def fmt_feixing(ch: dict, annual: int | None = None, month: tuple[int, int] | None = None,
                deg: float | None = None, yun_note: str = "") -> str:
    yun, sit, facing = ch["yun"], ch["sit"], ch["facing"]
    out = []
    out.append(f"【{yun}运 · {sit}山{facing}向】{'（替卦）' if ch['tigua'] else '（下卦）'}")
    if yun_note:
        out.append(yun_note)
    out.append(f"坐 {sit}山：{ch['sit_palace']}宫 {PALACE_DIR[ch['sit_palace']]}，"
               f"{YUANLONG[mountain_yuanlong(sit)]}龙，玄空阴阳 {mountain_yinyang(sit)}")
    out.append(f"向 {facing}山：{ch['face_palace']}宫 {PALACE_DIR[ch['face_palace']]}")
    if deg is not None:
        _, off = deg_to_mountain((deg + 180) % 360)
        out.append(f"罗盘：坐 {(deg + 180) % 360:.1f}° / 向 {deg:.1f}°，偏离{sit}山中线 {off:+.1f}°")
        out.extend(_jian_warnings(sit, off))
    for label, info in (("山星", ch["shan_info"]), ("向星", ch["xiang_info"])):
        n, by, fwd, rep = info
        why = f"依{by}山（{mountain_yinyang(by)}）" if n != 5 else f"五入中，依{by}山本身（{mountain_yinyang(by)}）"
        line = f"{label}：运盘 {n} 入中，{why} → {'顺飞' if fwd else '逆飞'}"
        if rep:
            line += f"；替卦以 {rep[1]} 代 {rep[0]} 入中"
        out.append(line)

    ann = fly(annual, True) if annual else None
    mon = fly(month[1], True) if month else None

    def cell(p):
        tag = PALACE_DIR[p]
        if p == ch["sit_palace"]:
            tag += "(坐)"
        if p == ch["face_palace"]:
            tag += "(向)"
        rows = [f"{p} {tag}", f"山{ch['shan'][p]} 向{ch['xiang'][p]}", f"运{ch['yunpan'][p]}"]
        extra = []
        if ann:
            extra.append(f"年{ann[p]}")
        if mon:
            extra.append(f"月{mon[p]}")
        if extra:
            rows.append(" ".join(extra))
        return rows

    out.append("")
    out.append("九宫（上南下北；山=山星管人丁，向=向星管财，运=运星）：")
    out.append(render_grid(cell, 16))
    out.append("")
    out.append("格局：" + ("；".join(ch["patterns"]) if ch["patterns"] else "无特殊格局（非旺山旺向/上山下水/双星）"))

    out.append("")
    out.append(f"{yun}运星曜旺衰：" + "，".join(f"{n}={star_status(n, yun)}" for n in range(1, 10)))
    if yun_of_year(_dt.date.today().year) != yun:
        cur = yun_of_year(_dt.date.today().year)
        out.append(f"（注：本盘为{yun}运盘；当前为{cur}运，论现时旺衰亦可参考{cur}运："
                   + "，".join(f"{n}={star_status(n, cur)}" for n in range(1, 10)) + "）")

    out.append("")
    out.append("各宫星组合：")
    for p in LUOSHU_PATH:
        s, x = ch["shan"][p], ch["xiang"][p]
        line = f"  {p}({PALACE_DIR[p]})：山{s}{STAR_NAMES[s][2:]} 向{x}{STAR_NAMES[x][2:]} 运{ch['yunpan'][p]}"
        flags = []
        if 5 in (s, x) or (ann and ann[p] == 5):
            flags.append("五黄")
        if {2, 5} <= {s, x, ann[p] if ann else 0}:
            flags.append("二五交加")
        if ann:
            line += f" 年{ann[p]}"
        if flags:
            line += "  ⚠ " + "、".join(dict.fromkeys(flags))
        out.append(line)
    return "\n".join(out)


def _jian_warnings(sit: str, off: float) -> list[str]:
    w = []
    a = abs(off)
    if a >= 6:
        nb = MOUNTAINS[(mountain_index(sit) + (1 if off > 0 else -1)) % 24]
        same_pal = mountain_palace(nb) == mountain_palace(sit)
        if same_pal:
            w.append(f"⚠ 接近{sit}/{nb}交界（小空亡，同宫异元龙），立向不清，宜复测")
        else:
            w.append(f"⚠ 接近{sit}/{nb}交界（大空亡，出卦），立向不清，宜复测")
    if a > 3:
        w.append("⚠ 兼向超过 3°，多数玄空派主张用替卦（--tigua）；各派兼向度数界限不一，宜两盘并参")
    return w


# ---------------------------------------------------------------------------
# 历法（需 lunar_python）
# ---------------------------------------------------------------------------

SHOUSI = dict(zip("寅卯辰巳午未申酉戌亥子丑", "戌辰亥巳子午丑未寅申卯酉"))  # 月支→受死日支
SIFEI = {  # 正四废：以节气月所在季论
    **dict.fromkeys("寅卯辰", ("庚申", "辛酉")),
    **dict.fromkeys("巳午未", ("壬子", "癸亥")),
    **dict.fromkeys("申酉戌", ("甲寅", "乙卯")),
    **dict.fromkeys("亥子丑", ("丙午", "丁巳")),
}

EVENTS = {
    # 事项: (黄历宜忌关键词, 首选建除, 次选建除)
    "入宅": (("入宅", "移徙"), "成开", "满定"),
    "搬家": (("移徙", "入宅"), "成开", "满定"),
    "开业": (("开市", "立券", "交易"), "开成", "满定"),
    "动土": (("动土", "修造"), "成开", "定"),
    "装修": (("修造", "动土"), "成开", "定"),
    "嫁娶": (("嫁娶",), "成开", "定满"),
    "订婚": (("订盟", "纳采"), "成开", "定满"),
    "安葬": (("安葬", "破土"), "成开", "除"),
    "出行": (("出行",), "成开", "定"),
    "签约": (("立券", "交易"), "定成", "开"),
    "安床": (("安床",), "定成", "开"),
}


def require_lunar():
    if not HAS_LUNAR:
        sys.exit("此命令需要历法库：pip install lunar_python")


def day_info(d: _dt.datetime) -> dict:
    require_lunar()
    sol = Solar.fromYmdHms(d.year, d.month, d.day, d.hour, d.minute, 0)
    lu = sol.getLunar()
    year_zhi = lu.getYearZhiByLiChun()
    month_zhi = lu.getMonthZhiExact()
    day_gz = lu.getDayInGanZhi()
    day_zhi = lu.getDayZhi()
    jianchu = lu.getZhiXing()
    flags = []
    if jianchu == "破":
        flags.append("月破")
    if ZHI.index(day_zhi) == (ZHI.index(year_zhi) + 6) % 12:
        flags.append("岁破")
    if SHOUSI[month_zhi] == day_zhi:
        flags.append("受死")
    if day_gz in SIFEI[month_zhi]:
        flags.append("正四废")
    prev_jq = lu.getPrevJieQi(True)
    return {
        "date": d,
        "lunar": f"{lu.getYearInChinese()}年{lu.getMonthInChinese()}月{lu.getDayInChinese()}",
        "year_gz": lu.getYearInGanZhiByLiChun(),
        "month_gz": lu.getMonthInGanZhiExact(),
        "day_gz": day_gz,
        "time_gz": lu.getTimeInGanZhi(),
        "jieqi": f"{prev_jq.getName()}（{prev_jq.getSolar().toYmd()}）后",
        "month_zhi": month_zhi,
        "jianchu": jianchu,
        "tianshen": f"{lu.getDayTianShen()}（{lu.getDayTianShenType()}）",
        "huangdao": lu.getDayTianShenType() == "黄道",
        "jishen": list(lu.getDayJiShen()),
        "xiongsha": list(lu.getDayXiongSha()),
        "yi": list(lu.getDayYi()),
        "ji": list(lu.getDayJi()),
        "chong": f"冲{lu.getDayChongDesc()}，煞{lu.getDaySha()}",
        "chong_zhi": ZHI[(ZHI.index(day_zhi) + 6) % 12],
        "flags": flags,
    }


def fmt_day(info: dict) -> str:
    d = info["date"]
    out = [f"【{d:%Y-%m-%d} 周{'一二三四五六日'[d.weekday()]}】农历{info['lunar']}",
           f"四柱：{info['year_gz']}年 {info['month_gz']}月 {info['day_gz']}日 {info['time_gz']}时（时柱按 {d:%H:%M}）",
           f"节气：{info['jieqi']}（月建 {info['month_zhi']}）",
           f"建除：{info['jianchu']}日    值神：{info['tianshen']}",
           f"{info['chong']}",
           f"吉神：{'、'.join(info['jishen']) or '—'}",
           f"凶煞：{'、'.join(info['xiongsha']) or '—'}",
           f"宜：{'、'.join(info['yi']) or '—'}",
           f"忌：{'、'.join(info['ji']) or '—'}"]
    if info["flags"]:
        out.append(f"⚠ 大忌：{'、'.join(info['flags'])}")
    return "\n".join(out)


def zeri(start: _dt.date, end: _dt.date, event: str, birth_years: list[int],
         top: int = 8) -> str:
    require_lunar()
    if event not in EVENTS:
        raise ValueError(f"事项应为：{'、'.join(EVENTS)}")
    keys, best, ok = EVENTS[event]
    person_zhi = {y: ZHI[(y - 4) % 12] for y in birth_years}
    good, bad = [], []
    d = start
    while d <= end:
        info = day_info(_dt.datetime(d.year, d.month, d.day, 12))
        reasons_bad = list(info["flags"])
        for y, z in person_zhi.items():
            if info["chong_zhi"] == z:
                reasons_bad.append(f"冲{y}年生人（{z}{SHENGXIAO[ZHI.index(z)]}）")
        if any(k in info["ji"] for k in keys):
            reasons_bad.append(f"黄历忌{'/'.join(k for k in keys if k in info['ji'])}")
        score, why = 0, []
        hit = [k for k in keys if k in info["yi"]]
        if hit:
            score += 3
            why.append(f"宜{'/'.join(hit)}")
        if info["jianchu"] in best:
            score += 2
            why.append(f"{info['jianchu']}日")
        elif info["jianchu"] in ok:
            score += 1
            why.append(f"{info['jianchu']}日(次)")
        if info["huangdao"]:
            score += 1
            why.append("黄道")
        de = [s for s in info["jishen"] if s in ("天德", "月德", "天德合", "月德合", "天赦", "天恩", "母仓")]
        if de:
            score += 2 if any(s in ("天德", "月德", "天赦") for s in de) else 1
            why.append("、".join(de))
        if reasons_bad:
            bad.append((d, info, reasons_bad))
        elif score >= 3:
            good.append((score, d, info, why))
        d += _dt.timedelta(days=1)

    good.sort(key=lambda t: (-t[0], t[1]))
    out = [f"【择日 · {event}】{start} 至 {end}"]
    if birth_years:
        out.append("当事人：" + "，".join(f"{y}年（{z}{SHENGXIAO[ZHI.index(z)]}）"
                                       for y, z in person_zhi.items()))
    ys = sorted({lichun_year(_dt.datetime(start.year, start.month, start.day))[0],
                 lichun_year(_dt.datetime(end.year, end.month, end.day))[0]})
    for y in ys:
        s = year_sha(y)
        out.append(f"{y}年{s['ganzhi']}：太岁{s['taisui']}，岁破{s['suipo']}，三煞{s['sansha']}，"
                   f"流年五黄{s['wuhuang']}、二黑{s['erhei']}")
    out.append("")
    out.append(f"候选吉日（按分数排序，共 {len(good)} 天合格，列前 {min(top, len(good))}）：")
    for score, d0, info, why in good[:top]:
        out.append(f"  {d0} 周{'一二三四五六日'[d0.weekday()]} {info['day_gz']}日 "
                   f"农历{info['lunar'].split('年')[1]}  分{score}：{'，'.join(why)}")
        out.append(f"      {info['chong']}；凶煞：{'、'.join(info['xiongsha'][:6]) or '—'}")
    if not good:
        out.append("  （范围内无合格日，建议放宽日期范围）")
    out.append("")
    out.append(f"已排除 {len(bad)} 天，例如：")
    for d0, info, rs in bad[:10]:
        out.append(f"  {d0} {info['day_gz']}日 {info['jianchu']}日：{'、'.join(rs)}")
    out.append("")
    out.append("说明：评分为筛选辅助（宜忌出自通书体系的黄历数据 + 建除 + 黄道 + 德神），"
               "月破/岁破/受死/正四废/冲当事人/黄历明忌为硬性排除。时辰与方位需另行配合。")
    return "\n".join(out)


def true_solar_time(d: _dt.datetime, longitude: float) -> tuple[_dt.datetime, float]:
    """北京时间 → 真太阳时（经度差 + 均时差）。返回 (校正后时间, 修正分钟)。"""
    n = d.timetuple().tm_yday
    b = math.radians(360 * (n - 81) / 364)
    eot = 9.87 * math.sin(2 * b) - 7.53 * math.cos(b) - 1.5 * math.sin(b)
    delta = (longitude - 120) * 4 + eot
    return d + _dt.timedelta(minutes=delta), delta


def bazi(d: _dt.datetime, gender: str, longitude: float | None) -> str:
    require_lunar()
    out = []
    if longitude is not None:
        d2, delta = true_solar_time(d, longitude)
        out.append(f"真太阳时：{d:%Y-%m-%d %H:%M} → {d2:%Y-%m-%d %H:%M}（经度 {longitude}°，修正 {delta:+.1f} 分钟）")
        d = d2
    lu = Solar.fromYmdHms(d.year, d.month, d.day, d.hour, d.minute, 0).getLunar()
    ec = lu.getEightChar()
    pillars = [ec.getYear(), ec.getMonth(), ec.getDay(), ec.getTime()]
    out.append(f"出生：{d:%Y-%m-%d %H:%M}（农历{lu.getYearInChinese()}年{lu.getMonthInChinese()}月{lu.getDayInChinese()}）")
    out.append("四柱：" + "  ".join(f"{n}{p}" for n, p in zip("年月日时", pillars)))
    out.append(f"日主：{ec.getDayGan()}（{wuxing_of(ec.getDayGan())}）  月令：{ec.getMonthZhi()}")
    out.append("十神（天干）：" + "  ".join([ec.getYearShiShenGan(), ec.getMonthShiShenGan(),
                                            "日主", ec.getTimeShiShenGan()]))
    out.append("藏干：" + "  ".join(f"{z}[{''.join(h)}]" for z, h in zip(
        [p[1] for p in pillars],
        [ec.getYearHideGan(), ec.getMonthHideGan(), ec.getDayHideGan(), ec.getTimeHideGan()])))
    out.append("纳音：" + "  ".join([ec.getYearNaYin(), ec.getMonthNaYin(), ec.getDayNaYin(), ec.getTimeNaYin()]))
    count = {k: 0 for k in "木火土金水"}
    for p in pillars:
        for ch in p:
            count[wuxing_of(ch)] += 1
    out.append("五行（八字表面计数，未计藏干与旺衰）：" + " ".join(f"{k}{v}" for k, v in count.items()))
    g = 1 if gender.lower() in ("m", "male", "男", "男命") else 0
    yun = ec.getYun(g)
    out.append(f"起运：出生后 {yun.getStartYear()}年{yun.getStartMonth()}月{yun.getStartDay()}天")
    dys = yun.getDaYun()[1:9]
    out.append("大运：" + "  ".join(f"{dy.getGanZhi()}({dy.getStartYear()})" for dy in dys))
    y_adj, _ = lichun_year(d)
    mg = mingua(y_adj, gender)
    out.append(f"命卦（八宅）：{mg} {NUM_PALACE[mg]}卦，{east_west(NUM_PALACE[mg])}命")
    out.append("注：日主强弱、格局、用神属于判断，需结合月令、通根、透干综合论断，本工具不代为判定。")
    return "\n".join(out)


WUXING = {**dict.fromkeys("甲乙寅卯", "木"), **dict.fromkeys("丙丁巳午", "火"),
          **dict.fromkeys("戊己辰戌丑未", "土"), **dict.fromkeys("庚辛申酉", "金"),
          **dict.fromkeys("壬癸亥子", "水")}


def wuxing_of(ch: str) -> str:
    return WUXING[ch]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _person_lines(birth: str, gender: str) -> tuple[list[str], str]:
    d = parse_date(birth)
    y, exact = lichun_year(d)
    n = mingua(y, gender)
    gua = NUM_PALACE[n]
    note = "" if exact else "（未装 lunar_python，按 2 月 4 日近似立春）"
    if len(birth.strip()) == 4:
        note = "（仅给年份：若生于立春前，应按上一年计）"
    lines = [f"出生 {birth}，{('男' if gender.lower() in ('m','male','男','男命') else '女')}命，"
             f"按立春计年 {y}{note}",
             f"命卦：{n} → {gua}卦（{'男命五寄坤' if n == 2 and mingua_raw(y, gender) == 5 else ''}"
             f"{'女命五寄艮' if n == 8 and mingua_raw(y, gender) == 5 else ''}），{east_west(gua)}命"]
    lines[-1] = lines[-1].replace("（）", "")
    return lines, gua


def mingua_raw(year: int, gender: str) -> int:
    g = gender.lower()
    if g in ("m", "male", "男", "男命"):
        return (11 - year % 9) % 9 or 9
    return (year % 9 + 4) % 9 or 9


def _younian_table(gua: str, title: str) -> list[str]:
    t = younian(gua)
    out = [title]
    for k in YOUNIAN_ORDER:
        p = t[k]
        out.append(f"  {k}：{PALACE_DIR[p]}（{p}）  {YOUNIAN_NOTE[k]}")
    return out


def cmd_mingua(a):
    lines, gua = _person_lines(a.birth, a.gender)
    print("\n".join(lines))
    print("\n".join(_younian_table(gua, f"{gua}命 四吉四凶方：")))


def cmd_bazhai(a):
    out = []
    house = None
    if a.sit or a.facing:
        if a.sit:
            sit, _ = parse_direction(a.sit)
        else:
            f, _ = parse_direction(a.facing)
            sit = opposite(f)
        house = mountain_palace(sit)
        out.append(f"宅：坐{sit}向{opposite(sit)} → 坐{PALACE_DIR[house]}，{house}宅（{east_west(house)}宅）")
        out += _younian_table(house, f"{house}宅 游年（以宅中心立极，看各方位）：")
    if a.birth:
        lines, gua = _person_lines(a.birth, a.gender)
        out.append("")
        out += lines
        out += _younian_table(gua, f"{gua}命 个人四吉四凶方（床头、书桌、门向参考）：")
        if house:
            same = east_west(house) == east_west(gua)
            out.append("")
            out.append(f"宅命配合：{east_west(house)}宅 × {east_west(gua)}命 → "
                       + ("相配" if same else "不配（可以个人吉方安排床位、书桌朝向作调整）"))
    if not out:
        sys.exit("请提供 --sit/--facing 或 --birth")
    print("\n".join(out))


def cmd_feixing(a):
    deg = None
    if a.sit:
        sit, sdeg = parse_direction(a.sit)
        if sdeg is not None:
            deg = (sdeg + 180) % 360
    elif a.facing:
        f, deg = parse_direction(a.facing)
        sit = opposite(f)
    else:
        sys.exit("请提供 --sit 或 --facing")
    note = ""
    if a.yun:
        yun = a.yun
    elif a.year:
        d = parse_date(a.year)
        y, _ = lichun_year(d)
        yun = yun_of_year(y)
        s, e = yun_range(yun)
        note = f"元运：{a.year} → {yun}运（{s}-{e}，以立春为界）。以入住或大修完工时间立极。"
    else:
        sys.exit("请提供 --yun 或 --year（入住/完工时间）")
    ch = feixing_chart(yun, sit, tigua=a.tigua)
    annual = month = None
    if a.annual:
        annual = annual_center(int(a.annual))
    if a.month:
        md = parse_date(a.month)
        y, mi = _month_index(md)
        month = (mi, monthly_center(y, mi))
        annual = annual or annual_center(y)
    print(fmt_feixing(ch, annual, month, deg, note))
    if annual:
        print(f"\n流年中宫 {annual}（{STAR_NAMES[annual]}）" +
              (f"，流月中宫 {month[1]}" if month else ""))


def _month_index(d: _dt.datetime) -> tuple[int, int]:
    """返回 (立春年, 节气月序 寅=1)。"""
    if HAS_LUNAR:
        lu = Solar.fromYmdHms(d.year, d.month, d.day, d.hour, 0, 0).getLunar()
        mz = lu.getMonthZhiExact()
        y, _ = lichun_year(d)
        return y, (ZHI.index(mz) - 2) % 12 + 1
    # 近似：每月 6 日前后交节
    y, _ = lichun_year(d)
    mi = (d.month - 2 - (1 if d.day < 6 else 0)) % 12 + 1
    return y, mi


def cmd_liunian(a):
    years = range(a.year, a.year + a.span)
    for y in years:
        c = annual_center(y)
        s = year_sha(y)
        ann = fly(c, True)
        print(f"【{y} {s['ganzhi']}年】中宫 {STAR_NAMES[c]}；五黄 {s['wuhuang']}，二黑 {s['erhei']}；"
              f"太岁 {s['taisui']}，岁破 {s['suipo']}，三煞 {s['sansha']}")
        if a.span == 1:
            print(render_grid(lambda p: [f"{p} {PALACE_DIR[p]}", f"{STAR_NAMES[ann[p]]}"], 14))
            print("流月中宫（寅月起）：" + " ".join(
                f"{ZHI[(i + 1) % 12]}月{monthly_center(y, i)}" for i in range(1, 13)))


def cmd_day(a):
    d = parse_date(a.date)
    if len(a.date.strip()) <= 10:
        d = d.replace(hour=12)
    info = day_info(d)
    print(fmt_day(info))
    y, _ = lichun_year(d)
    s = year_sha(y)
    print(f"年家：太岁{s['taisui']}，岁破{s['suipo']}，三煞{s['sansha']}，流年五黄{s['wuhuang']}")


def cmd_zeri(a):
    s, e = parse_date(a.start).date(), parse_date(a.end).date()
    if (e - s).days > 400:
        sys.exit("范围过大（>400 天）")
    print(zeri(s, e, a.event, a.birth_year or [], a.top))


def cmd_bazi(a):
    print(bazi(parse_date(a.birth), a.gender, a.longitude))


def main(argv=None):
    p = argparse.ArgumentParser(prog="fengshui.py", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("mingua", help="命卦")
    s.add_argument("--birth", required=True, help="出生日期 YYYY-MM-DD（仅年份亦可，但立春前出生需注意）")
    s.add_argument("--gender", required=True, help="m/f 或 男/女")
    s.set_defaults(func=cmd_mingua)

    s = sub.add_parser("bazhai", help="八宅游年")
    s.add_argument("--sit", help="坐山（山名或度数）")
    s.add_argument("--facing", help="向首（山名或罗盘度数）")
    s.add_argument("--birth")
    s.add_argument("--gender", default="m")
    s.set_defaults(func=cmd_bazhai)

    s = sub.add_parser("feixing", help="玄空飞星排盘")
    s.add_argument("--sit", help="坐山（山名或坐度）")
    s.add_argument("--facing", help="向首（山名或向度，推荐给罗盘度数）")
    s.add_argument("--yun", type=int, help="直接指定元运 1-9")
    s.add_argument("--year", help="入住/完工日期或年份，用于定运")
    s.add_argument("--tigua", action="store_true", help="用替卦（兼向时）")
    s.add_argument("--annual", help="叠加流年（年份）")
    s.add_argument("--month", help="叠加流月（日期，按节气月）")
    s.set_defaults(func=cmd_feixing)

    s = sub.add_parser("liunian", help="流年紫白与年家煞方")
    s.add_argument("--year", type=int, required=True)
    s.add_argument("--span", type=int, default=1, help="连续列出几年")
    s.set_defaults(func=cmd_liunian)

    s = sub.add_parser("day", help="某日历法信息")
    s.add_argument("--date", required=True, help="YYYY-MM-DD 或 'YYYY-MM-DD HH:MM'")
    s.set_defaults(func=cmd_day)

    s = sub.add_parser("zeri", help="择日筛选")
    s.add_argument("--event", required=True, help="、".join(EVENTS))
    s.add_argument("--start", required=True)
    s.add_argument("--end", required=True)
    s.add_argument("--birth-year", type=int, action="append", help="当事人出生年（可多次）")
    s.add_argument("--top", type=int, default=8)
    s.set_defaults(func=cmd_zeri)

    s = sub.add_parser("bazi", help="八字排盘")
    s.add_argument("--birth", required=True, help="'YYYY-MM-DD HH:MM'（北京时间）")
    s.add_argument("--gender", required=True)
    s.add_argument("--longitude", type=float, help="出生地经度，给出则换算真太阳时")
    s.set_defaults(func=cmd_bazi)

    a = p.parse_args(argv)
    try:
        a.func(a)
    except ValueError as e:
        sys.exit(f"错误：{e}")


if __name__ == "__main__":
    main()
