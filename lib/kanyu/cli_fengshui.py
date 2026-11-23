"""fengshui-master 的命令：命卦、八宅、飞星、流年、单日、择日。解析参数 → 调用计算模块 → 交给 render 输出（或 --json）。"""

from __future__ import annotations

import argparse
import sys

from . import __version__, cli, pages, pages_feixing, render
from .almanac import day_info, has_time, lichun_year, month_index, parse_date
from .bazhai import east_west, mingua_of, younian
from .cli import Output, UsageError, _jsonable
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

八字已移至独立的 bazi-mingli skill（skills/bazi-mingli/scripts/bazi.py）。

飞星 / 八宅 / 命卦只依赖标准库；历法相关命令（day / zeri，
以及按立春精确分年）需要 `pip install lunar_python`。
加 --json 输出结构化数据。
"""

BAZI_MOVED = ("八字已移至独立的 bazi-mingli skill。安装：npx skills add voidforall/fengshui.skill --skill bazi-mingli；"
              "安装后运行该 skill 的 scripts/bazi.py --birth ... --gender ...")


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
        note = pages_feixing.yun_note(a.year, yun, s, e)
    else:
        raise UsageError("请提供 --yun 或 --year（入住/完工时间）")

    ch = feixing_chart(yun, sit, tigua=a.tigua)
    annual = annual_center(int(a.annual)) if a.annual else None
    month = None
    if a.month:
        y, mi = month_index(parse_date(a.month))
        month = monthly_center(y, mi)
        annual = annual or annual_center(y)
    cur = yun_of_year(cli.today().year)
    text = render.feixing(ch, annual=annual, month=month, facing_deg=facing_deg, yun_note=note,
                          current_yun=cur)
    data = {"chart": _jsonable(ch), "facing_deg": facing_deg, "annual_center": annual, "month_center": month}
    if a.html is not None:
        notes = pages_feixing.load_notes(a.notes)
        ann_year = a.annual or (lichun_year(parse_date(a.month))[0] if a.month else None)
        annual_label = None if ann_year is None else (str(ann_year) if a.lang == "en" else f"{ann_year}年")
        page_note = pages_feixing.yun_note(a.year, yun, *yun_range(yun), lang=a.lang) if a.year and not a.yun else ""
        page = pages.render("feixing.html", pages_feixing.page_title(ch, a.lang),
                            pages_feixing.feixing_data(ch, annual=annual, annual_label=annual_label, month=month,
                                               facing_deg=facing_deg, yun_note=page_note, current_yun=cur,
                                               notes=notes, lang=a.lang),
                            lang=a.lang)
        path = pages.write_page(a.html or pages_feixing.default_name(ch, a.lang), page)
        text += f"\n\n交互盘面已生成：{path}"
        data["html"] = path
    elif a.notes or a.lang != "zh":
        raise UsageError("--notes、--lang 需与 --html 一起使用")
    return Output(text, data)


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
    s.add_argument("--html", nargs="?", const="", metavar="PATH",
                   help="同时生成可交互的 HTML 盘面（不给路径则写到当前目录）")
    s.add_argument("--notes", metavar="JSON", help="写入盘面的批注：{summary, palaces:{宫名:文字}, advice:[...]}")
    s.add_argument("--lang", choices=pages_feixing.LANGS, default="zh",
                   help="盘面语言：zh 中文（默认）/ en 英文；批注用同一种语言写")

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

    return p


def main(argv=None) -> None:
    """fengshui-master 的入口：python3 scripts/fengshui.py <子命令> ..."""
    argv = sys.argv[1:] if argv is None else argv
    if argv[:1] == ["bazi"]:
        sys.exit(BAZI_MOVED)
    cli.execute(argv, build_parser())
