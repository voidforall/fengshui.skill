"""八字排盘（依赖 lunar_python）。只做计算，不判定强弱用神。"""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass, field

from .bazhai import MinGua, mingua_of
from .almanac import lichun_year, require_lunar, true_solar_time
from .core import parse_gender, wuxing_of

try:
    from lunar_python import Solar  # type: ignore
except ImportError:  # pragma: no cover
    Solar = None


@dataclass
class DaYun:
    ganzhi: str
    start_year: int


@dataclass
class Bazi:
    input_time: _dt.datetime
    birth: _dt.datetime                 # 实际排盘所用时间（可能已换真太阳时）
    longitude: float | None
    solar_delta: float | None           # 真太阳时修正分钟
    lunar: str
    pillars: list[str]                  # 年 月 日 时
    day_gan: str
    month_zhi: str
    shishen_gan: list[str]              # 年 月 日 时 天干十神（日为「日主」）
    hide_gan: list[list[str]]
    nayin: list[str]
    wuxing_count: dict[str, int]
    qiyun: tuple[int, int, int]         # 起运：年 月 天
    dayun: list[DaYun] = field(default_factory=list)
    mingua: MinGua | None = None


def wuxing_count(pillars: list[str]) -> dict[str, int]:
    count = {k: 0 for k in "木火土金水"}
    for p in pillars:
        for ch in p:
            count[wuxing_of(ch)] += 1
    return count


def bazi(d: _dt.datetime, gender: str, longitude: float | None = None) -> Bazi:
    require_lunar()
    g = parse_gender(gender)
    t, delta = (true_solar_time(d, longitude) if longitude is not None else (d, None))
    lu = Solar.fromYmdHms(t.year, t.month, t.day, t.hour, t.minute, 0).getLunar()
    ec = lu.getEightChar()
    pillars = [ec.getYear(), ec.getMonth(), ec.getDay(), ec.getTime()]
    yun = ec.getYun(1 if g == "m" else 0)
    return Bazi(
        input_time=d,
        birth=t,
        longitude=longitude,
        solar_delta=delta,
        lunar=f"{lu.getYearInChinese()}年{lu.getMonthInChinese()}月{lu.getDayInChinese()}",
        pillars=pillars,
        day_gan=ec.getDayGan(),
        month_zhi=ec.getMonthZhi(),
        shishen_gan=[ec.getYearShiShenGan(), ec.getMonthShiShenGan(), "日主", ec.getTimeShiShenGan()],
        hide_gan=[list(ec.getYearHideGan()), list(ec.getMonthHideGan()),
                  list(ec.getDayHideGan()), list(ec.getTimeHideGan())],
        nayin=[ec.getYearNaYin(), ec.getMonthNaYin(), ec.getDayNaYin(), ec.getTimeNaYin()],
        wuxing_count=wuxing_count(pillars),
        qiyun=(yun.getStartYear(), yun.getStartMonth(), yun.getStartDay()),
        dayun=[DaYun(dy.getGanZhi(), dy.getStartYear()) for dy in yun.getDaYun()[1:9]],
        mingua=mingua_of(lichun_year(t)[0], g),
    )
