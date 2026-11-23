"""历法：日期解析、立春分年、节气月、单日信息、真太阳时。

lunar_python 为可选依赖：未安装时，立春按 2 月 4 日近似、节气月按每月 6 日近似，
单日信息（day_info）不可用。
"""

from __future__ import annotations

import datetime as _dt
import math
from dataclasses import dataclass, field

from .core import ZHI, chong, ganzhi_of_year

try:
    from lunar_python import Solar  # type: ignore

    HAS_LUNAR = True
except ImportError:  # pragma: no cover - 取决于环境
    Solar = None
    HAS_LUNAR = False


class LunarUnavailable(RuntimeError):
    """需要 lunar_python 而未安装。"""

    def __init__(self):
        super().__init__("此命令需要历法库：pip install lunar_python")


def require_lunar() -> None:
    if not HAS_LUNAR:
        raise LunarUnavailable()


def _solar(d: _dt.date | _dt.datetime):
    if isinstance(d, _dt.datetime):
        return Solar.fromYmdHms(d.year, d.month, d.day, d.hour, d.minute, d.second)
    return Solar.fromYmdHms(d.year, d.month, d.day, 12, 0, 0)


# --- 日期解析 ------------------------------------------------------------------

_DATE_FORMATS = ("%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M", "%Y-%m-%d", "%Y/%m/%d", "%Y%m%d")


def parse_date(s: str) -> _dt.datetime:
    """YYYY-MM-DD[ HH:MM] / YYYY/MM/DD / YYYYMMDD；仅给年份时取当年 6 月 1 日。"""
    s = s.strip()
    for fmt in _DATE_FORMATS:
        try:
            return _dt.datetime.strptime(s, fmt)
        except ValueError:
            pass
    if s.isdigit() and len(s) == 4:
        return _dt.datetime(int(s), 6, 1)
    raise ValueError(f"无法解析日期 {s!r}（格式 YYYY-MM-DD 或 'YYYY-MM-DD HH:MM'）")


def has_time(s: str) -> bool:
    return len(s.strip()) > 10


def lunar_to_solar(d: _dt.datetime, leap: bool = False) -> _dt.datetime:
    """农历（年 月 日，时分照搬）→ 公历。闰月须 leap=True。"""
    require_lunar()
    from lunar_python import Lunar  # type: ignore
    try:
        s = Lunar.fromYmdHms(d.year, -d.month if leap else d.month, d.day, d.hour, d.minute, 0).getSolar()
    except Exception as e:   # lunar_python 对不存在的日期抛 Exception
        raise ValueError(f"农历 {d.year} 年{'闰' if leap else ''}{d.month} 月 {d.day} 日不存在：{e}") from None
    return _dt.datetime(s.getYear(), s.getMonth(), s.getDay(), d.hour, d.minute)


# --- 立春分年 / 节气月 ------------------------------------------------------------

def lichun_year(d: _dt.date | _dt.datetime) -> tuple[int, bool]:
    """返回以立春为界的年份，以及是否精确（False 表示按 2 月 4 日近似）。"""
    if HAS_LUNAR:
        gz = _solar(d).getLunar().getYearInGanZhiByLiChun()
        for y in (d.year, d.year - 1):  # 由干支反推年份（离公历年至多差 1）
            if ganzhi_of_year(y) == gz:
                return y, True
    approx = d.year if (d.month, d.day) >= (2, 4) else d.year - 1
    return approx, False


def month_index(d: _dt.datetime) -> tuple[int, int]:
    """返回 (立春年, 节气月序 寅=1 … 丑=12)。"""
    y, _ = lichun_year(d)
    if HAS_LUNAR:
        mz = Solar.fromYmdHms(d.year, d.month, d.day, d.hour, 0, 0).getLunar().getMonthZhiExact()
        return y, (ZHI.index(mz) - 2) % 12 + 1
    # 近似：每月 6 日前后交节
    return y, (d.month - 2 - (1 if d.day < 6 else 0)) % 12 + 1


# --- 单日信息 -------------------------------------------------------------------

SHOUSI = dict(zip("寅卯辰巳午未申酉戌亥子丑", "戌辰亥巳子午丑未寅申卯酉"))  # 月支→受死日支
SIFEI = {  # 正四废：以节气月所在季论
    **dict.fromkeys("寅卯辰", ("庚申", "辛酉")),
    **dict.fromkeys("巳午未", ("壬子", "癸亥")),
    **dict.fromkeys("申酉戌", ("甲寅", "乙卯")),
    **dict.fromkeys("亥子丑", ("丙午", "丁巳")),
}


@dataclass
class DayInfo:
    date: _dt.datetime
    lunar: str                 # 农历日期（中文）
    year_gz: str               # 以立春为界
    month_gz: str              # 以节气为界
    day_gz: str
    time_gz: str
    jieqi: str                 # 所在节气说明
    month_zhi: str
    jianchu: str               # 建除十二神
    tianshen: str              # 值神（黄道/黑道）
    huangdao: bool
    jishen: list[str] = field(default_factory=list)
    xiongsha: list[str] = field(default_factory=list)
    yi: list[str] = field(default_factory=list)
    ji: list[str] = field(default_factory=list)
    chong: str = ""            # 冲煞描述
    chong_zhi: str = ""        # 本日所冲地支
    flags: list[str] = field(default_factory=list)   # 大忌（《协纪辨方书》体系）：月破、正四废
    suji: list[str] = field(default_factory=list)    # 通书俗忌（无《协纪》出处）：岁破日、受死

    @property
    def lunar_md(self) -> str:
        return self.lunar.split("年", 1)[1]


def day_flags(year_zhi: str, month_zhi: str, day_gz: str, jianchu: str) -> tuple[list[str], list[str]]:
    """返回 (大忌, 通书俗忌)。纯规则，便于单独测试；出处见 references/sources.md。

    大忌：月破、正四废 ——《协纪辨方书》所载，且与 lunar-python 逐日一致。
    俗忌：岁破日（日支冲太岁）、受死 —— 通书用法，《协纪》体系日神中未列，只作提示。
    """
    day_zhi = day_gz[1]
    flags, suji = [], []
    if jianchu == "破":
        flags.append("月破")
    if day_gz in SIFEI[month_zhi]:
        flags.append("正四废")
    if day_zhi == chong(year_zhi):
        suji.append("岁破日")
    if SHOUSI[month_zhi] == day_zhi:
        suji.append("受死")
    return flags, suji


def day_info(d: _dt.datetime) -> DayInfo:
    require_lunar()
    lu = Solar.fromYmdHms(d.year, d.month, d.day, d.hour, d.minute, 0).getLunar()
    month_zhi = lu.getMonthZhiExact()
    day_gz = lu.getDayInGanZhi()
    jianchu = lu.getZhiXing()
    prev_jq = lu.getPrevJieQi(True)
    info = DayInfo(
        date=d,
        lunar=f"{lu.getYearInChinese()}年{lu.getMonthInChinese()}月{lu.getDayInChinese()}",
        year_gz=lu.getYearInGanZhiByLiChun(),
        month_gz=lu.getMonthInGanZhiExact(),
        day_gz=day_gz,
        time_gz=lu.getTimeInGanZhi(),
        jieqi=f"{prev_jq.getName()}（{prev_jq.getSolar().toYmd()}）后",
        month_zhi=month_zhi,
        jianchu=jianchu,
        tianshen=f"{lu.getDayTianShen()}（{lu.getDayTianShenType()}）",
        huangdao=lu.getDayTianShenType() == "黄道",
        jishen=list(lu.getDayJiShen()),
        xiongsha=list(lu.getDayXiongSha()),
        yi=list(lu.getDayYi()),
        ji=list(lu.getDayJi()),
        chong=f"冲{lu.getDayChongDesc()}，煞{lu.getDaySha()}",
        chong_zhi=chong(lu.getDayZhi()),
    )
    info.flags, info.suji = day_flags(lu.getYearZhiByLiChun(), month_zhi, day_gz, jianchu)
    return info


# --- 真太阳时 -------------------------------------------------------------------

def equation_of_time(d: _dt.date) -> float:
    """均时差（分钟），常用近似式。"""
    n = d.timetuple().tm_yday
    b = math.radians(360 * (n - 81) / 364)
    return 9.87 * math.sin(2 * b) - 7.53 * math.cos(b) - 1.5 * math.sin(b)


def true_solar_time(d: _dt.datetime, longitude: float, std_meridian: float = 120) -> tuple[_dt.datetime, float]:
    """当地标准时 → 真太阳时（经度差 + 均时差）。默认北京时间（东经 120° 标准时）。返回 (校正后时间, 修正分钟)。"""
    delta = (longitude - std_meridian) * 4 + equation_of_time(d)
    return (d + _dt.timedelta(minutes=delta)).replace(microsecond=0), delta


# --- 出生时刻：时区、夏令时、真太阳时 ---------------------------------------------------

DEFAULT_TZ = "Asia/Shanghai"


@dataclass
class BirthMoment:
    clock: _dt.datetime            # 用户给的钟表时间（时辰不详时为当日正午）
    tz: str
    time_known: bool
    dst_minutes: int               # 当时实行夏令时则为 60（钟表比标准时快）
    std_offset_minutes: int        # 当地标准时与 UTC 之差
    standard: _dt.datetime         # 当地标准时 = 钟表时间 - 夏令时
    beijing: _dt.datetime          # 同一时刻的北京时间（UTC+8），用于比对节气、立春
    longitude: float | None
    solar: _dt.datetime | None     # 真太阳时（给了经度才有）
    solar_delta: float | None      # 真太阳时相对当地标准时的修正分钟
    notes: list[str] = field(default_factory=list)

    @property
    def local(self) -> _dt.datetime:
        """排日柱、时柱所用的当地时间：有经度用真太阳时，否则用当地标准时。"""
        return self.solar or self.standard


def _zone(tz: str) -> _dt.tzinfo:
    import re
    m = re.fullmatch(r"(?:UTC|GMT)?([+-])(\d{1,2})(?::?(\d{2}))?", tz.strip())
    if m:
        mins = int(m.group(2)) * 60 + int(m.group(3) or 0)
        return _dt.timezone(_dt.timedelta(minutes=mins if m.group(1) == "+" else -mins))
    try:
        from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
    except ImportError:  # pragma: no cover - Python < 3.9
        raise ValueError("当前 Python 不支持时区名，请改用 UTC+8 之类的固定偏移") from None
    try:
        return ZoneInfo(tz)
    except (ZoneInfoNotFoundError, ValueError):
        raise ValueError(f"未知时区 {tz!r}：请用 IANA 时区名（如 Asia/Shanghai、America/New_York）"
                         "或 UTC+8 之类的固定偏移；Windows 需先 pip install tzdata") from None


def birth_moment(clock: _dt.datetime, tz: str = DEFAULT_TZ, longitude: float | None = None,
                 time_known: bool = True) -> BirthMoment:
    """把出生地钟表时间换算为：当地标准时（扣夏令时）、北京时间（比节气）、真太阳时（排时柱）。

    中国大陆 1986–1991 年实行夏令时，其间 4–9 月出生者钟表时间比标准时快 1 小时；
    时区库（IANA tzdata）记有各地历史夏令时，据此扣除。
    """
    zone = _zone(tz)
    aware = clock.replace(tzinfo=zone)
    utc = aware.astimezone(_dt.timezone.utc)
    notes = []
    if utc.astimezone(zone).replace(tzinfo=None) != clock and time_known:
        notes.append(f"{clock:%Y-%m-%d %H:%M} 在当地夏令时切换中不存在（钟表拨快的那一小时），请核对出生时间")
    dst = aware.dst() or _dt.timedelta(0)
    std = (aware.utcoffset() or _dt.timedelta(0)) - dst
    standard = clock - dst
    beijing = (utc + _dt.timedelta(hours=8)).replace(tzinfo=None)
    dst_min = int(dst.total_seconds() // 60)
    solar = delta = None
    if longitude is not None:
        if not -180 <= longitude <= 180:
            raise ValueError("经度应在 -180 到 180 之间（东经为正）")
        solar, delta = true_solar_time(standard, longitude, std.total_seconds() / 240)
    return BirthMoment(clock=clock, tz=tz, time_known=time_known, dst_minutes=dst_min,
                       std_offset_minutes=int(std.total_seconds() // 60), standard=standard, beijing=beijing,
                       longitude=longitude, solar=solar, solar_delta=delta, notes=notes)
