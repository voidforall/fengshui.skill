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
    flags: list[str] = field(default_factory=list)  # 大忌：月破 / 岁破 / 受死 / 正四废

    @property
    def lunar_md(self) -> str:
        return self.lunar.split("年", 1)[1]


def day_flags(year_zhi: str, month_zhi: str, day_gz: str, jianchu: str) -> list[str]:
    """大忌判定（纯规则，便于单独测试）。"""
    day_zhi = day_gz[1]
    flags = []
    if jianchu == "破":
        flags.append("月破")
    if day_zhi == chong(year_zhi):
        flags.append("岁破")
    if SHOUSI[month_zhi] == day_zhi:
        flags.append("受死")
    if day_gz in SIFEI[month_zhi]:
        flags.append("正四废")
    return flags


def day_info(d: _dt.datetime) -> DayInfo:
    require_lunar()
    lu = Solar.fromYmdHms(d.year, d.month, d.day, d.hour, d.minute, 0).getLunar()
    month_zhi = lu.getMonthZhiExact()
    day_gz = lu.getDayInGanZhi()
    jianchu = lu.getZhiXing()
    prev_jq = lu.getPrevJieQi(True)
    return DayInfo(
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
        flags=day_flags(lu.getYearZhiByLiChun(), month_zhi, day_gz, jianchu),
    )


# --- 真太阳时 -------------------------------------------------------------------

def equation_of_time(d: _dt.date) -> float:
    """均时差（分钟），常用近似式。"""
    n = d.timetuple().tm_yday
    b = math.radians(360 * (n - 81) / 364)
    return 9.87 * math.sin(2 * b) - 7.53 * math.cos(b) - 1.5 * math.sin(b)


def true_solar_time(d: _dt.datetime, longitude: float) -> tuple[_dt.datetime, float]:
    """北京时间 → 真太阳时（经度差 + 均时差）。返回 (校正后时间, 修正分钟)。"""
    delta = (longitude - 120) * 4 + equation_of_time(d)
    return d + _dt.timedelta(minutes=delta), delta
