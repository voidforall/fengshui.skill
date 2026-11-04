"""命令行入口。解析参数 → 调用计算模块 → 交给 render 输出（或 --json）。"""

from __future__ import annotations

import argparse
import dataclasses
import datetime as _dt
import json
import sys

from . import __version__, render
from .almanac import LunarUnavailable, day_info, has_time, lichun_year, month_index, parse_date
from .bazhai import east_west, mingua_of, younian
from .bazi import bazi
from .core import mountain_palace, opposite, parse_direction, yun_of_year, yun_range
from .feixing import feixing_chart
from .zeri import EVENTS, select
from .zibai import annual_center, monthly_center, year_sha

DESCRIPTION = """堪舆确定性计算工具 —— 供 fengshui-master skill 调用。

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
加 --json 输出结构化数据。
"""


class UsageError(Exception):
    pass


def today() -> _dt.date:
    """当前日期（单独成函数，便于测试替换）。"""
    return _dt.date.today()


# --- 结果：文本 + 结构化数据 ---------------------------------------------------------

@dataclasses.dataclass
class Output:
    text: str
    data: object


def _jsonable(o):
    if dataclasses.is_dataclass(o) and not isinstance(o, type):
        d = {f.name: _jsonable(getattr(o, f.name)) for f in dataclasses.fields(o)}
        for name in ("replaced", "jigong", "label"):   # 常用派生属性也带上
            if hasattr(type(o), name) and isinstance(getattr(type(o), name), property):
                d[name] = _jsonable(getattr(o, name))
        return d
    if isinstance(o, dict):
        return {str(k): _jsonable(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_jsonable(v) for v in o]
    if isinstance(o, (_dt.date, _dt.datetime)):
        return o.isoformat()
    return o


# --- 子命令 ------------------------------------------------------------------------

def _person(birth: str, gender: str):
    y, exact = lichun_year(parse_date(birth))
    note = "" if exact else "（未装 lunar_python，按 2 月 4 日近似立春）"
    if len(birth.strip()) == 4:
        note = "（仅给年份：若生于立春前，应按上一年计）"
    mg = mingua_of(y, gender)
    return mg, render.person(birth, mg, note), {"birth": birth, "lichun_exact": exact, **_jsonable(mg)}


def _youniandict(gua: str) -> dict:
    return {k: v for k, v in younian(gua).items()}


def cmd_mingua(a) -> Output:
    mg, lines, data = _person(a.birth, a.gender)
    lines += render.younian_table(mg.gua, f"{mg.gua}命 四吉四凶方：")
    return Output("\n".join(lines), {**data, "younian": _youniandict(mg.gua)})


def cmd_bazhai(a) -> Output:
    if not (a.sit or a.facing or a.birth):
        raise UsageError("请提供 --sit/--facing 或 --birth")
    out, data, house = [], {}, None
    if a.sit or a.facing:
        sit = parse_direction(a.sit)[0] if a.sit else opposite(parse_direction(a.facing)[0])
        house = mountain_palace(sit)
        out += render.house(sit, opposite(sit), house, east_west(house))
        out += render.younian_table(house, f"{house}宅 游年（以宅中心立极，看各方位）：")
        data["house"] = {"sit": sit, "facing": opposite(sit), "gua": house,
                         "group": east_west(house), "younian": _youniandict(house)}
    if a.birth:
        mg, lines, pdata = _person(a.birth, a.gender)
        out += [""] + lines
        out += render.younian_table(mg.gua, f"{mg.gua}命 个人四吉四凶方（床头、书桌、门向参考）：")
        data["person"] = {**pdata, "younian": _youniandict(mg.gua)}
        if house:
            out += ["", render.match(east_west(house), mg.group)]
            data["match"] = east_west(house) == mg.group
    return Output("\n".join(out), data)


def cmd_feixing(a) -> Output:
    facing_deg = None
    if a.sit:
        sit, sdeg = parse_direction(a.sit)
        if sdeg is not None:
            facing_deg = (sdeg + 180) % 360
    elif a.facing:
        f, facing_deg = parse_direction(a.facing)
        sit = opposite(f)
    else:
        raise UsageError("请提供 --sit 或 --facing")

    note = ""
    if a.yun:
        yun = a.yun
    elif a.year:
        y, _ = lichun_year(parse_date(a.year))
        yun = yun_of_year(y)
        s, e = yun_range(yun)
        note = f"元运：{a.year} → {yun}运（{s}-{e}，以立春为界）。以入住或大修完工时间立极。"
    else:
        raise UsageError("请提供 --yun 或 --year（入住/完工时间）")

    ch = feixing_chart(yun, sit, tigua=a.tigua)
    annual = annual_center(int(a.annual)) if a.annual else None
    month = None
    if a.month:
        y, mi = month_index(parse_date(a.month))
        month = monthly_center(y, mi)
        annual = annual or annual_center(y)
    text = render.feixing(ch, annual=annual, month=month, facing_deg=facing_deg, yun_note=note,
                          current_yun=yun_of_year(today().year))
    return Output(text, {"chart": _jsonable(ch), "facing_deg": facing_deg,
                         "annual_center": annual, "month_center": month})


def cmd_liunian(a) -> Output:
    out, data = [], []
    for y in range(a.year, a.year + a.span):
        s = year_sha(y)
        out.append(render.year_line(s))
        if a.span == 1:
            out.append(render.year_detail(s))
        data.append({**_jsonable(s), "months": [monthly_center(y, i) for i in range(1, 13)]})
    return Output("\n".join(out), data)


def cmd_day(a) -> Output:
    d = parse_date(a.date)
    if not has_time(a.date):
        d = d.replace(hour=12)
    info = day_info(d)
    ys = year_sha(lichun_year(d)[0])
    return Output(render.day(info, ys), {"day": _jsonable(info), "year": _jsonable(ys)})


def cmd_zeri(a) -> Output:
    r = select(parse_date(a.start).date(), parse_date(a.end).date(), a.event, a.birth_year or [])
    data = _jsonable(r)
    data["good"] = data["good"][:a.top]
    return Output(render.zeri(r, a.top), data)


def cmd_bazi(a) -> Output:
    b = bazi(parse_date(a.birth), a.gender, a.longitude)
    return Output(render.bazi(b), _jsonable(b))


# --- 参数 --------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--json", action="store_true", help="输出结构化 JSON")

    p = argparse.ArgumentParser(prog="fengshui.py", description=DESCRIPTION,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    def add(name, func, help_):
        s = sub.add_parser(name, help=help_, parents=[common])
        s.set_defaults(func=func)
        return s

    s = add("mingua", cmd_mingua, "命卦")
    s.add_argument("--birth", required=True, help="出生日期 YYYY-MM-DD（仅年份亦可，但立春前出生需注意）")
    s.add_argument("--gender", required=True, help="m/f 或 男/女")

    s = add("bazhai", cmd_bazhai, "八宅游年")
    s.add_argument("--sit", help="坐山（山名或度数）")
    s.add_argument("--facing", help="向首（山名或罗盘度数）")
    s.add_argument("--birth")
    s.add_argument("--gender", default="m")

    s = add("feixing", cmd_feixing, "玄空飞星排盘")
    s.add_argument("--sit", help="坐山（山名或坐度）")
    s.add_argument("--facing", help="向首（山名或向度，推荐给罗盘度数）")
    s.add_argument("--yun", type=int, choices=range(1, 10), metavar="1-9", help="直接指定元运")
    s.add_argument("--year", help="入住/完工日期或年份，用于定运")
    s.add_argument("--tigua", action="store_true", help="用替卦（兼向时）")
    s.add_argument("--annual", help="叠加流年（年份）")
    s.add_argument("--month", help="叠加流月（日期，按节气月）")

    s = add("liunian", cmd_liunian, "流年紫白与年家煞方")
    s.add_argument("--year", type=int, required=True)
    s.add_argument("--span", type=int, default=1, help="连续列出几年")

    s = add("day", cmd_day, "某日历法信息")
    s.add_argument("--date", required=True, help="YYYY-MM-DD 或 'YYYY-MM-DD HH:MM'")

    s = add("zeri", cmd_zeri, "择日筛选")
    s.add_argument("--event", required=True, help="、".join(EVENTS))
    s.add_argument("--start", required=True)
    s.add_argument("--end", required=True)
    s.add_argument("--birth-year", type=int, action="append", help="当事人出生年（可多次）")
    s.add_argument("--top", type=int, default=8)

    s = add("bazi", cmd_bazi, "八字排盘")
    s.add_argument("--birth", required=True, help="'YYYY-MM-DD HH:MM'（北京时间）")
    s.add_argument("--gender", required=True)
    s.add_argument("--longitude", type=float, help="出生地经度，给出则换算真太阳时")
    return p


def run(argv=None) -> tuple[Output, argparse.Namespace]:
    """解析并执行，返回 (Output, args)；出错抛异常（供测试调用）。"""
    a = build_parser().parse_args(argv)
    return a.func(a), a


def main(argv=None) -> None:
    try:
        out, a = run(argv)
    except LunarUnavailable as e:
        sys.exit(str(e))
    except UsageError as e:
        sys.exit(str(e))
    except ValueError as e:
        sys.exit(f"错误：{e}")
    if a.json:
        print(json.dumps(_jsonable(out.data), ensure_ascii=False, indent=2))
    else:
        print(out.text)
