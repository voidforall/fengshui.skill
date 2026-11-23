"""择日筛选：硬排除 + 打分。依赖 almanac.day_info（lunar_python）。"""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass, field

from .almanac import DayInfo, day_info, lichun_year, require_lunar
from .core import shengxiao, zhi_of_year
from .zibai import YearSha, year_sha


@dataclass(frozen=True)
class Event:
    keys: tuple[str, ...]   # 黄历宜忌关键词
    best: str               # 首选建除
    ok: str                 # 次选建除


EVENTS = {
    "入宅": Event(("入宅", "移徙"), "成开", "满定"),
    "搬家": Event(("移徙", "入宅"), "成开", "满定"),
    "开业": Event(("开市", "立券", "交易"), "开成", "满定"),
    "动土": Event(("动土", "修造"), "成开", "定"),
    "装修": Event(("修造", "动土"), "成开", "定"),
    "嫁娶": Event(("嫁娶",), "成开", "定满"),
    "订婚": Event(("订盟", "纳采"), "成开", "定满"),
    "安葬": Event(("安葬", "破土"), "成开", "除"),
    "出行": Event(("出行",), "成开", "定"),
    "签约": Event(("立券", "交易"), "定成", "开"),
    "安床": Event(("安床",), "定成", "开"),
}

# 计分权重
SCORE_YI = 3            # 黄历明宜该事
SCORE_BEST = 2          # 首选建除
SCORE_OK = 1            # 次选建除
SCORE_HUANGDAO = 1
DE_SHEN = ("天德", "月德", "天德合", "月德合", "天赦", "天恩", "母仓")
DE_SHEN_MAJOR = ("天德", "月德", "天赦")   # 有其一 +2，否则 +1
MIN_SCORE = 3
MAX_RANGE_DAYS = 400


@dataclass
class Person:
    year: int
    zhi: str

    @property
    def label(self) -> str:
        return f"{self.year}年（{self.zhi}{shengxiao(self.zhi)}）"


@dataclass
class DayScore:
    info: DayInfo
    score: int = 0
    reasons: list[str] = field(default_factory=list)    # 加分理由
    excluded: list[str] = field(default_factory=list)   # 排除原因（非空即排除）
    notes: list[str] = field(default_factory=list)      # 不排除、但须向用户说明的通书俗忌


@dataclass
class ZeriResult:
    event: str
    start: _dt.date
    end: _dt.date
    persons: list[Person]
    years: list[YearSha]
    good: list[DayScore]        # 已按分数排序
    bad: list[DayScore]


def get_event(name: str) -> Event:
    if name not in EVENTS:
        raise ValueError(f"事项应为：{'、'.join(EVENTS)}")
    return EVENTS[name]


def score_day(info: DayInfo, ev: Event, persons: list[Person]) -> DayScore:
    ds = DayScore(info)
    ds.excluded = list(info.flags)
    ds.notes = [f"通书俗忌：{x}" for x in info.suji]
    for p in persons:
        if info.chong_zhi == p.zhi:
            ds.excluded.append(f"冲{p.year}年生人（{p.zhi}{shengxiao(p.zhi)}）")
    ji_hit = [k for k in ev.keys if k in info.ji]
    if ji_hit:
        ds.excluded.append(f"黄历忌{'/'.join(ji_hit)}")

    yi_hit = [k for k in ev.keys if k in info.yi]
    if yi_hit:
        ds.score += SCORE_YI
        ds.reasons.append(f"宜{'/'.join(yi_hit)}")
    if info.jianchu in ev.best:
        ds.score += SCORE_BEST
        ds.reasons.append(f"{info.jianchu}日")
    elif info.jianchu in ev.ok:
        ds.score += SCORE_OK
        ds.reasons.append(f"{info.jianchu}日(次)")
    if info.huangdao:
        ds.score += SCORE_HUANGDAO
        ds.reasons.append("黄道")
    de = [s for s in info.jishen if s in DE_SHEN]
    if de:
        ds.score += 2 if any(s in DE_SHEN_MAJOR for s in de) else 1
        ds.reasons.append("、".join(de))
    return ds


def select(start: _dt.date, end: _dt.date, event: str, birth_years: list[int]) -> ZeriResult:
    require_lunar()
    ev = get_event(event)
    if (end - start).days > MAX_RANGE_DAYS:
        raise ValueError(f"范围过大（>{MAX_RANGE_DAYS} 天）")
    persons = [Person(y, zhi_of_year(y)) for y in birth_years]
    good, bad = [], []
    d = start
    while d <= end:
        ds = score_day(day_info(_dt.datetime(d.year, d.month, d.day, 12)), ev, persons)
        if ds.excluded:
            bad.append(ds)
        elif ds.score >= MIN_SCORE:
            good.append(ds)
        d += _dt.timedelta(days=1)
    good.sort(key=lambda t: (-t.score, t.info.date))
    years = sorted({lichun_year(_dt.datetime(x.year, x.month, x.day))[0] for x in (start, end)})
    return ZeriResult(event, start, end, persons, [year_sha(y) for y in years], good, bad)
