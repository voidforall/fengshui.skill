"""玄空飞星：排盘、格局判定、兼向提示。纯标准库。"""

from __future__ import annotations

from dataclasses import dataclass, field

from .core import (LUOSHU_PATH, MOUNTAINS, NUM_PALACE, fly, mountain_palace,
                   mountain_yinyang, mountain_yuanlong, neighbor, opposite, palace_mountain)

# 替卦（《沈氏玄空学》替卦诀）：
#   子癸甲申贪狼一路行；坤壬乙卯未巨门从头出；
#   戌乾亥辰巽巳武曲位；艮丙辛酉丑破军；寅午庚丁右弼。
TIGUA_STAR: dict[str, int] = {}
for _ms, _n in [("子癸甲申", 1), ("坤壬乙卯未", 2), ("戌乾亥辰巽巳", 6),
                ("艮丙辛酉丑", 7), ("寅午庚丁", 9)]:
    for _m in _ms:
        TIGUA_STAR[_m] = _n
assert len(TIGUA_STAR) == 24 and set(TIGUA_STAR) == set(MOUNTAINS)


@dataclass
class StarEntry:
    """山星或向星入中的推导过程。"""
    n: int                    # 运盘落在坐/向宫的星
    by: str                   # 定顺逆所依之山
    forward: bool             # 顺飞？
    center: int               # 实际入中之星（替卦时为替星）

    @property
    def replaced(self) -> bool:
        return self.center != self.n


@dataclass
class Chart:
    yun: int
    sit: str
    facing: str
    sit_palace: str
    face_palace: str
    tigua: bool
    yunpan: dict[str, int]
    shan: dict[str, int]
    xiang: dict[str, int]
    shan_entry: StarEntry
    xiang_entry: StarEntry
    patterns: list[str] = field(default_factory=list)


def star_direction(n: int, ref_mountain: str) -> tuple[bool, str]:
    """入中之星 n 的顺逆：取 n 原宫中与 ref_mountain 同元龙之山的阴阳。

    n == 5 无宫可归，以 ref_mountain（坐山或向首）本身阴阳论。
    返回 (是否顺飞, 用以定阴阳的山)。
    """
    if n == 5:
        m = ref_mountain
    else:
        m = palace_mountain(NUM_PALACE[n], mountain_yuanlong(ref_mountain))
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


def _entry(yunpan: dict[str, int], palace: str, ref: str, tigua: bool) -> StarEntry:
    n = yunpan[palace]
    forward, by = star_direction(n, ref)
    center = TIGUA_STAR[by] if (tigua and n != 5) else n
    return StarEntry(n, by, forward, center)


def feixing_chart(yun: int, sit: str, tigua: bool = False) -> Chart:
    facing = opposite(sit)
    sit_pal, face_pal = mountain_palace(sit), mountain_palace(facing)
    yunpan = fly(yun, True)
    se = _entry(yunpan, sit_pal, sit, tigua)
    xe = _entry(yunpan, face_pal, facing, tigua)
    ch = Chart(yun, sit, facing, sit_pal, face_pal, tigua, yunpan,
               fly(se.center, se.forward), fly(xe.center, xe.forward), se, xe)
    ch.patterns = chart_patterns(ch)
    return ch


def _consecutive(t) -> bool:
    return any({(a + k - 1) % 9 + 1 for k in range(3)} == set(t) for a in range(1, 10))


def chart_patterns(ch: Chart) -> list[str]:
    yun, shan, xiang, yunpan = ch.yun, ch.shan, ch.xiang, ch.yunpan
    pats = []
    s_sit, s_face = shan[ch.sit_palace], shan[ch.face_palace]
    x_sit, x_face = xiang[ch.sit_palace], xiang[ch.face_palace]
    if s_sit == yun and x_face == yun:
        pats.append("旺山旺向（当令山星到坐、向星到向）")
    elif s_face == yun and x_sit == yun:
        pats.append("上山下水（当令山星到向、向星到坐）")
    elif s_face == yun and x_face == yun:
        pats.append("双星到向（当令山向二星同到向首）")
    elif s_sit == yun and x_sit == yun:
        pats.append("双星到坐（当令山向二星同到坐山）")

    for name, e in (("山星", ch.shan_entry), ("向星", ch.xiang_entry)):
        if e.center == 5:
            pats.append(f"{name}伏吟（五入中顺飞，与洛书元旦盘相同）" if e.forward
                        else f"{name}反吟（五入中逆飞，与洛书元旦盘相反）")

    if all(shan[p] + yunpan[p] == 10 for p in LUOSHU_PATH):
        pats.append("山星与运星合十")
    if all(xiang[p] + yunpan[p] == 10 for p in LUOSHU_PATH):
        pats.append("向星与运星合十")
    groups = [{1, 4, 7}, {2, 5, 8}, {3, 6, 9}]
    if all({yunpan[p], shan[p], xiang[p]} in groups for p in LUOSHU_PATH):
        pats.append("父母三般卦（每宫运山向三星成 147/258/369）")
    if all(_consecutive((yunpan[p], shan[p], xiang[p])) for p in LUOSHU_PATH):
        pats.append("连珠三般卦（每宫运山向三星相连）")
    return pats


def main_pattern(ch: Chart) -> str | None:
    """四大格局之一（旺山旺向 / 上山下水 / 双星到向 / 双星到坐），否则 None。"""
    for p in ch.patterns:
        if "当令" in p:
            return p.split("（")[0]
    return None


def palace_flags(shan: int, xiang: int, annual: int | None = None) -> list[str]:
    """某宫的凶星提示。"""
    flags = []
    if 5 in (shan, xiang) or annual == 5:
        flags.append("五黄")
    if {2, 5} <= {shan, xiang, annual or 0}:
        flags.append("二五交加")
    return flags


def jian_warnings(sit: str, off: float) -> list[str]:
    """按偏离坐山中线的度数给出兼向 / 空亡提示。"""
    w = []
    a = abs(off)
    if a >= 6:
        nb = neighbor(sit, 1 if off > 0 else -1)
        if mountain_palace(nb) == mountain_palace(sit):
            w.append(f"⚠ 接近{sit}/{nb}交界（小空亡，同宫异元龙），立向不清，宜复测")
        else:
            w.append(f"⚠ 接近{sit}/{nb}交界（大空亡，出卦），立向不清，宜复测")
    if a > 3:
        w.append("⚠ 兼向超过 3°，多数玄空派主张用替卦（--tigua）；各派兼向度数界限不一，宜两盘并参")
    return w

