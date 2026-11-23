"""bazi-mingli 的命令：八字排盘。解析参数 → 调用 bazi → 交给 render_bazi 输出（或 --json），可生成交互命盘。"""

from __future__ import annotations

import argparse
import sys

from . import __version__, cli, pages, pages_bazi, render_bazi
from .almanac import has_time, lunar_to_solar, parse_date
from .bazi import bazi
from .cli import Output, UsageError, _jsonable

BAZI_DESCRIPTION = """八字确定性计算工具 —— 供 bazi-mingli skill 调用。

排盘、查表、历法由脚本完成：四柱、藏干十神、十二长生、月令司令、通根透干、合冲刑害、
查表神煞、《穷通宝鉴》调候原文、起运与大运流年；可同时生成交互命盘（--html）。
不判定日主旺衰、格局、用神。需要 `pip install lunar_python`。加 --json 输出结构化数据。
"""


def cmd_bazi(a) -> Output:
    if len(a.birth.strip()) == 4:
        raise UsageError("八字至少需要出生年月日：--birth YYYY-MM-DD（时辰不详时只给日期）")
    d = parse_date(a.birth)
    if a.leap and not a.lunar:
        raise UsageError("--leap 需与 --lunar 一起使用")
    if a.lunar:
        d = lunar_to_solar(d, a.leap)
    b = bazi(d, a.gender, a.longitude, tz=a.tz, time_known=has_time(a.birth),
             zi=a.zi, focus_year=a.year or cli.today().year)
    text, data = render_bazi.bazi(b), _jsonable(b)
    if a.lunar:
        note = f"农历输入：{a.birth.strip()[:10]}{'（闰月）' if a.leap else ''} → 公历 {d:%Y-%m-%d}"
        text = note + "\n" + text
        data["lunar_input"] = note
    if a.html is not None:
        notes = pages_bazi.load_bazi_notes(a.notes)
        page = pages.render("bazi.html", pages_bazi.bazi_title(b, a.lang),
                            pages_bazi.bazi_data(b, notes=notes, lang=a.lang), lang=a.lang)
        path = pages.write_page(a.html or pages_bazi.bazi_default_name(b, a.lang), page)
        text += f"\n\n交互命盘已生成：{path}"
        data["html"] = path
    elif a.notes or a.lang != "zh":
        raise UsageError("--notes、--lang 需与 --html 一起使用")
    return Output(text, data)


def add_args(s: argparse.ArgumentParser) -> None:
    s.add_argument("--birth", required=True,
                   help="出生地钟表时间 'YYYY-MM-DD HH:MM'；时辰不详只给 YYYY-MM-DD（排三柱）")
    s.add_argument("--gender", required=True)
    s.add_argument("--longitude", type=float, help="出生地经度（东经为正），给出则按真太阳时排时柱")
    s.add_argument("--lunar", action="store_true", help="--birth 为农历日期（月、日用数字，如 1990-04-26 08:30）")
    s.add_argument("--leap", action="store_true", help="农历闰月（与 --lunar 一起用）")
    s.add_argument("--tz", default="Asia/Shanghai",
                   help="出生地时区（IANA 名或 UTC+8），默认 Asia/Shanghai；据此自动扣夏令时")
    s.add_argument("--zi", choices=["next", "same"], default="next",
                   help="子时口径：next=23:00 起换日（默认）；same=晚子时日柱仍按当日")
    s.add_argument("--year", type=int, help="重点看的流年（默认今年）")
    s.add_argument("--html", nargs="?", const="", metavar="PATH",
                   help="同时生成可交互的命盘 HTML（不给路径则写到当前目录）")
    s.add_argument("--notes", metavar="JSON",
                   help="写入命盘的批注：{summary, basis, pillars:{年月日时:文字}, dayun:{干支:文字}, years:{年份:文字}, advice:[...]}")
    s.add_argument("--lang", choices=pages_bazi.LANGS, default="zh",
                   help="命盘语言：zh 中文（默认）/ en 英文；批注用同一种语言写")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="bazi.py", description=BAZI_DESCRIPTION,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--version", action="version", version=f"%(prog)s（kanyu {__version__}）")
    p.add_argument("--json", action="store_true", help="输出结构化 JSON")
    add_args(p)
    p.set_defaults(func=cmd_bazi)
    return p


def main(argv=None) -> None:
    """bazi-mingli 的入口：python3 scripts/bazi.py --birth ... --gender ..."""
    cli.execute(sys.argv[1:] if argv is None else argv, build_parser())
