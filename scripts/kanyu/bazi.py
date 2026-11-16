"""八字排盘（依赖 lunar_python）。只做计算与查表，不判定旺衰、格局、用神。

时间口径：
- 年柱、月柱以「同一时刻的北京时间」比对立春与节气（lunar-python 的节气表为北京时间）；
- 日柱、时柱用出生地当地时间：给了经度用真太阳时，否则用当地标准时（已扣夏令时）；
- 子时换日：默认 23:00 起换日（next）；可选 same（晚子时日柱仍按当日、时干按次日起）。
"""

from __future__ import annotations

import datetime as _dt
import json
import os
from dataclasses import dataclass, field

from . import ganzhi as gzr
from .almanac import BirthMoment, birth_moment, lichun_year, require_lunar
from .bazhai import MinGua, mingua_of
from .core import ganzhi_of_year, jiazi_step, parse_gender, wuxing_of

try:
    from lunar_python import Solar  # type: ignore
    from lunar_python.util import LunarUtil  # type: ignore
except ImportError:  # pragma: no cover
    Solar = LunarUtil = None

ZI_RULES = {"next": "23:00 起换日（子初换日）", "same": "晚子时（23:00–24:00）日柱仍按当日，时干按次日起"}
_DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "qiongtong.json")


@dataclass
class Hidden:
    gan: str
    qi: str            # 本气 / 中气 / 余气
    shishen: str


@dataclass
class Pillar:
    name: str          # 年 月 日 时
    ganzhi: str
    gan_shishen: str   # 日柱为「日主」
    hidden: list[Hidden]
    nayin: str
    changsheng: str    # 日干在此支的十二长生
    xunkong: str       # 本柱所在旬的空亡

    @property
    def gan(self) -> str:
        return self.ganzhi[0]

    @property
    def zhi(self) -> str:
        return self.ganzhi[1]


@dataclass
class LiuNian:
    year: int
    ganzhi: str
    age: int           # 当年生日后的周岁
    gan_shishen: str
    changsheng: str
    relations: list[str]


@dataclass
class DaYun:
    ganzhi: str
    start: _dt.date            # 交运日期
    start_age: tuple[int, int]  # 交运时周岁（年, 月）
    gan_shishen: str
    zhi_shishen: str           # 地支本气十神
    changsheng: str
    relations: list[str]
    years: list[LiuNian] = field(default_factory=list)

    @property
    def start_year(self) -> int:
        return self.start.year


@dataclass
class Bazi:
    moment: BirthMoment
    gender: str
    zi_rule: str
    lunar: str
    pillars: list[Pillar]              # 年 月 日 [时]；时辰不详时只有三柱
    day_gan: str
    month_zhi: str
    zi_alt: dict | None                # 23 点后出生：另一种子时口径的日柱、时柱
    siling: dict                       # 月令人元司事
    roots: list[dict]                  # 天干通根
    tou: list[dict]                    # 地支藏干透出
    relations: dict                    # 原局 {"gan": [...], "zhi": [...]}
    wuxing_count: dict[str, int]       # 天干地支表面计数
    wuxing_hidden: dict[str, int]      # 藏干出现次数
    shensha: list[dict]
    tiaohou: dict                      # 《穷通宝鉴》本日干、本月令原文
    qiyun: tuple[int, int, int]        # 起运：出生后 年 月 天
    qiyun_date: _dt.date
    dayun: list[DaYun]
    focus_year: int
    focus: LiuNian | None              # 关注年份的流年（默认今年）
    focus_dayun: str | None            # 关注年份所在大运；起运前为 None
    mingua: MinGua
    warnings: list[str] = field(default_factory=list)

    @property
    def input_time(self) -> _dt.datetime:
        return self.moment.clock

    @property
    def birth(self) -> _dt.datetime:
        return self.moment.local

    @property
    def time_known(self) -> bool:
        return self.moment.time_known

    @property
    def ganzhi(self) -> list[str]:
        return [p.ganzhi for p in self.pillars]


# --- 纯规则部分（不依赖历法库） -------------------------------------------------------

def dayun_forward(year_gan: str, gender: str) -> bool:
    """大运顺逆：阳年生男、阴年生女顺排；阴年生男、阳年生女逆排。

    🧮 一次性核对《滴天髓阐微》485 个命例，书中所列大运全部一致。
    """
    yang = year_gan in "甲丙戊庚壬"
    return yang == (parse_gender(gender) == "m")


def dayun_from_pillars(pillars: list[str], gender: str, n: int = 8) -> list[str]:
    """由四柱与性别排大运干支：自月柱起，顺则依六十甲子向后，逆则向前，共 n 步。

    只排干支，不算起运岁数（起运岁数需出生时刻，见 bazi()）。纯规则，不依赖历法库。
    """
    k = 1 if dayun_forward(pillars[0][0], gender) else -1
    return [jiazi_step(pillars[1], k * (i + 1)) for i in range(n)]


def wuxing_count(pillars: list[str]) -> dict[str, int]:
    count = {k: 0 for k in "木火土金水"}
    for p in pillars:
        for ch in p:
            count[wuxing_of(ch)] += 1
    return count


def wuxing_hidden(pillars: list[str]) -> dict[str, int]:
    count = {k: 0 for k in "木火土金水"}
    for p in pillars:
        for g in gzr.HIDE_GAN[p[1]]:
            count[wuxing_of(g)] += 1
    return count


def make_pillar(name: str, gz: str, day_gan: str, nayin: str) -> Pillar:
    return Pillar(
        name=name, ganzhi=gz,
        gan_shishen="日主" if name == "日" else gzr.shishen(day_gan, gz[0]),
        hidden=[Hidden(g, gzr.QI_NAMES[i], gzr.shishen(day_gan, g)) for i, g in enumerate(gzr.HIDE_GAN[gz[1]])],
        nayin=nayin, changsheng=gzr.changsheng(day_gan, gz[1]), xunkong=gzr.xunkong(gz),
    )


def roots_and_tou(pillars: list[str]) -> tuple[list[dict], list[dict]]:
    """通根：天干在哪些地支的藏干中有同五行者；透干：地支藏干在天干中原样出现。纯事实，不论力量。"""
    names = gzr.PILLAR_NAMES
    roots, tou = [], []
    for i, p in enumerate(pillars):
        rs = []
        for j, q in enumerate(pillars):
            for k, h in enumerate(gzr.HIDE_GAN[q[1]]):
                if wuxing_of(h) == wuxing_of(p[0]):
                    rs.append({"pillar": names[j], "zhi": q[1], "hidden": h, "qi": gzr.QI_NAMES[k]})
        roots.append({"pillar": names[i], "gan": p[0], "roots": rs})
    stems = [p[0] for p in pillars]
    for j, q in enumerate(pillars):
        for k, h in enumerate(gzr.HIDE_GAN[q[1]]):
            at = [names[i] for i, s in enumerate(stems) if s == h]
            if at:
                tou.append({"pillar": names[j], "zhi": q[1], "hidden": h, "qi": gzr.QI_NAMES[k], "at": at})
    return roots, tou


def natal_relations(pillars: list[str]) -> dict:
    names = gzr.PILLAR_NAMES
    gan = gzr.relations([(names[i] + "干", p[0]) for i, p in enumerate(pillars)])
    zhi = gzr.relations([(names[i] + "支", p[1]) for i, p in enumerate(pillars)])
    for r in gan + zhi:
        r["label"] = gzr.relation_label(r)
    return {"gan": gan, "zhi": zhi}


_QT = None


def tiaohou(day_gan: str, month_zhi: str) -> dict:
    """《穷通宝鉴》本日干、本月令（节气月）原文段落。数据由 evals/tools/build_qiongtong.py 生成。"""
    global _QT
    if _QT is None:
        with open(_DATA, encoding="utf-8") as f:
            _QT = json.load(f)
    cell = _QT["cells"][day_gan + month_zhi]
    return {**cell, "book": "《穷通宝鉴》", "url": _QT["url"]}


def liunian(year: int, natal: list[str], day_gan: str, birth_year: int) -> LiuNian:
    gz = ganzhi_of_year(year)
    return LiuNian(year=year, ganzhi=gz, age=year - birth_year, gan_shishen=gzr.shishen(day_gan, gz[0]),
                   changsheng=gzr.changsheng(day_gan, gz[1]), relations=gzr.against_natal(gz, natal, "流年"))


def _add_years(d: _dt.date, n: int) -> _dt.date:
    try:
        return d.replace(year=d.year + n)
    except ValueError:      # 2 月 29 日
        return d.replace(year=d.year + n, day=28)


# --- 排盘 ---------------------------------------------------------------------------

def _solar(d: _dt.datetime):
    return Solar.fromYmdHms(d.year, d.month, d.day, d.hour, d.minute, d.second)


def bazi(d: _dt.datetime, gender: str, longitude: float | None = None, *, tz: str = "Asia/Shanghai",
         time_known: bool = True, zi: str = "next", focus_year: int | None = None, n_dayun: int = 10) -> Bazi:
    require_lunar()
    if zi not in ZI_RULES:
        raise ValueError("子时口径应为 next 或 same")
    g = parse_gender(gender)
    if not time_known:
        d = d.replace(hour=12, minute=0, second=0)
    m = birth_moment(d, tz, longitude if time_known else None, time_known)
    warnings = list(m.notes)
    if not time_known and longitude is not None:
        warnings.append("时辰不详，不作真太阳时换算")

    # 年、月：北京时间比对节气
    lu_abs = _solar(m.beijing).getLunar()
    ec_abs = lu_abs.getEightChar()
    year_gz, month_gz = ec_abs.getYear(), ec_abs.getMonth()

    # 日、时：当地时间
    local = m.local

    def day_time(sect: int) -> tuple[str, str]:
        ec = _solar(local).getLunar().getEightChar()
        ec.setSect(sect)
        return ec.getDay(), ec.getTime()

    day_gz, time_gz = day_time(1 if zi == "next" else 2)
    zi_alt = None
    if time_known and local.hour == 23:
        other = "same" if zi == "next" else "next"
        od, ot = day_time(1 if other == "next" else 2)
        zi_alt = {"rule": other, "rule_desc": ZI_RULES[other], "day": od, "time": ot}
        warnings.append(f"生于 23 点后，子时换日两派说法并存。本盘取「{ZI_RULES[zi]}」：日柱{day_gz}、时柱{time_gz}；"
                        f"另一说「{ZI_RULES[other]}」：日柱{od}、时柱{ot}（加 --zi {other} 可按此排）")

    gz_list = [year_gz, month_gz, day_gz] + ([time_gz] if time_known else [])
    day_gan, month_zhi = day_gz[0], month_gz[1]
    lu_loc = _solar(local).getLunar()
    pillars = [make_pillar(n, p, day_gan, LunarUtil.NAYIN[p]) for n, p in zip(gzr.PILLAR_NAMES, gz_list)]

    if not time_known:
        for jq in (lu_abs.getPrevJie(False), lu_abs.getNextJie(False)):
            if jq.getSolar().toYmd() == f"{m.beijing:%Y-%m-%d}":
                warnings.append(f"出生当日交{jq.getName()}（{jq.getSolar().toYmdHms()[11:16]} 北京时间），"
                                "时辰不详时月柱" + ("、年柱" if jq.getName() == "立春" else "") + "可能不准")

    # 月令司令：交节后第几日
    jie = lu_abs.getPrevJie(False)
    js = jie.getSolar()
    jie_dt = _dt.datetime(js.getYear(), js.getMonth(), js.getDay(), js.getHour(), js.getMinute(), js.getSecond())
    day_n = int((m.beijing - jie_dt).total_seconds() // 86400) + 1
    siling = {"jie": jie.getName(), "jie_time": jie_dt, "day_n": day_n,
              "ruler": gzr.siling(month_zhi, day_n),
              "table": [{"name": n, "days": k} for n, k in gzr.SILING[month_zhi]]}

    roots, tou = roots_and_tou(gz_list)

    # 起运、大运
    yun = ec_abs.getYun(1 if g == "m" else 0)
    qy = (yun.getStartYear(), yun.getStartMonth(), yun.getStartDay())
    ss = yun.getStartSolar()
    qy_date = _dt.date(ss.getYear(), ss.getMonth(), ss.getDay())
    if not time_known:
        warnings.append("时辰不详：起运按当日正午估算，误差约两个月以内")
    birth_year = m.clock.year
    focus_year = focus_year or _dt.date.today().year
    dayun, focus_dayun = [], None
    for k, dy in enumerate(yun.getDaYun(n_dayun + 1)[1:]):
        gz = dy.getGanZhi()
        start = _add_years(qy_date, 10 * k)
        item = DaYun(ganzhi=gz, start=start, start_age=(qy[0] + 10 * k, qy[1]),
                     gan_shishen=gzr.shishen(day_gan, gz[0]),
                     zhi_shishen=gzr.shishen(day_gan, gzr.HIDE_GAN[gz[1]][0]),
                     changsheng=gzr.changsheng(day_gan, gz[1]),
                     relations=gzr.against_natal(gz, gz_list, "大运"),
                     years=[liunian(start.year + i, gz_list, day_gan, birth_year) for i in range(10)])
        if any(y.year == focus_year for y in item.years):
            focus_dayun = gz
        dayun.append(item)
    focus = liunian(focus_year, gz_list, day_gan, birth_year) if focus_year >= birth_year else None

    return Bazi(
        moment=m, gender=g, zi_rule=zi,
        lunar=f"{lu_loc.getYearInChinese()}年{lu_loc.getMonthInChinese()}月{lu_loc.getDayInChinese()}",
        pillars=pillars, day_gan=day_gan, month_zhi=month_zhi, zi_alt=zi_alt, siling=siling,
        roots=roots, tou=tou, relations=natal_relations(gz_list),
        wuxing_count=wuxing_count(gz_list), wuxing_hidden=wuxing_hidden(gz_list),
        shensha=gzr.shensha(gz_list),
        tiaohou=tiaohou(day_gan, month_zhi),
        qiyun=qy, qiyun_date=qy_date, dayun=dayun,
        focus_year=focus_year, focus=focus, focus_dayun=focus_dayun,
        mingua=mingua_of(lichun_year(m.beijing)[0], g),
        warnings=warnings,
    )
