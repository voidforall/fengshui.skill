"""流年流月紫白、年家煞方。纯标准库。"""

from __future__ import annotations

from dataclasses import dataclass

from .core import PALACE_DIR, ZHI_DIR, chong, fly, ganzhi_of_year, palace_of_star, zhi_of_year


def annual_center(year: int) -> int:
    """流年中宫星（年份以立春为界）。如 2024=三碧、2025=二黑、2026=一白。"""
    return (10 - year % 9) % 9 + 1


_MONTH_START = {**dict.fromkeys("子午卯酉", 8), **dict.fromkeys("辰戌丑未", 5),
                **dict.fromkeys("寅申巳亥", 2)}


def monthly_center(year: int, month_index: int) -> int:
    """流月中宫星。month_index: 寅月=1 … 丑月=12（节气月）。

    子午卯酉年寅月起八白，辰戌丑未年起五黄，寅申巳亥年起二黑，逐月逆减。
    """
    start = _MONTH_START[zhi_of_year(year)]
    return (start - 1 - (month_index - 1)) % 9 + 1


SANSHA = {  # 三煞方（以年支三合局论）
    **dict.fromkeys("申子辰", ("南", "巳午未")),
    **dict.fromkeys("寅午戌", ("北", "亥子丑")),
    **dict.fromkeys("亥卯未", ("西", "申酉戌")),
    **dict.fromkeys("巳酉丑", ("东", "寅卯辰")),
}


@dataclass
class YearSha:
    year: int
    ganzhi: str
    center: int        # 流年中宫星
    taisui: str        # 例：南（午山）
    suipo: str
    sansha: str        # 例：北（亥子丑）
    wuhuang: str       # 流年五黄方位
    erhei: str         # 流年二黑方位


def year_sha(year: int) -> YearSha:
    zhi = zhi_of_year(year)
    po = chong(zhi)
    c = annual_center(year)
    ann = fly(c, True)
    return YearSha(
        year=year,
        ganzhi=ganzhi_of_year(year),
        center=c,
        taisui=f"{ZHI_DIR[zhi]}（{zhi}山）",
        suipo=f"{ZHI_DIR[po]}（{po}山）",
        sansha=f"{SANSHA[zhi][0]}（{SANSHA[zhi][1]}）",
        wuhuang=PALACE_DIR[palace_of_star(ann, 5)],
        erhei=PALACE_DIR[palace_of_star(ann, 2)],
    )
