"""八宅明镜：命卦、游年。纯标准库（立春分年见 almanac）。"""

from __future__ import annotations

from dataclasses import dataclass

from .core import NUM_PALACE, parse_gender

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


def east_west(gua: str) -> str:
    return "东四" if gua in EAST_FOUR else "西四"


def mingua_raw(year: int, gender: str) -> int:
    """未寄宫的命卦数（1–9）。"""
    if parse_gender(gender) == "m":
        return (11 - year % 9) % 9 or 9
    return (year % 9 + 4) % 9 or 9


def mingua(year: int, gender: str) -> int:
    """命卦数（年份须已按立春调整）。男命五寄坤(2)，女命五寄艮(8)。"""
    n = mingua_raw(year, gender)
    if n == 5:
        return 2 if parse_gender(gender) == "m" else 8
    return n


@dataclass
class MinGua:
    year: int          # 按立春调整后的年份
    gender: str        # 'm' / 'f'
    raw: int           # 未寄宫数
    number: int        # 命卦数
    gua: str           # 卦名
    group: str         # 东四 / 西四

    @property
    def jigong(self) -> str:
        if self.raw != 5:
            return ""
        return "男命五寄坤" if self.gender == "m" else "女命五寄艮"


def mingua_of(year: int, gender: str) -> MinGua:
    g = parse_gender(gender)
    n = mingua(year, g)
    gua = NUM_PALACE[n]
    return MinGua(year, g, mingua_raw(year, g), n, gua, east_west(gua))
