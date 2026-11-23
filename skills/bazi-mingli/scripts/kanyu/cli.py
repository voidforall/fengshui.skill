"""命令行公共部分：结果对象、JSON 化、解析与执行。

各 skill 的命令在 cli_fengshui.py（fengshui-master）与 cli_bazi.py（bazi-mingli）；
入口脚本分别是各 skill 的 scripts/fengshui.py、scripts/bazi.py。
"""

from __future__ import annotations

import argparse
import dataclasses
import datetime as _dt
import json
import sys

from .almanac import LunarUnavailable


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


def run(argv=None, parser: argparse.ArgumentParser | None = None) -> tuple[Output, argparse.Namespace]:
    """解析并执行，返回 (Output, args)；出错抛异常（供测试调用）。

    不给 parser 时按第一个参数选择：`bazi ...` 走八字命令，其余走风水命令。
    （仓库测试用；安装后的 skill 只带自己那一部分命令。）
    """
    if parser is None:
        argv = list(sys.argv[1:] if argv is None else argv)
        if argv[:1] == ["bazi"]:
            from .cli_bazi import build_parser as build
            argv = argv[1:]
        else:
            from .cli_fengshui import build_parser as build
        parser = build()
    a = parser.parse_args(argv)
    return a.func(a), a


def execute(argv, parser: argparse.ArgumentParser) -> None:
    """命令行执行：打印文字或 JSON；常见错误转为一行提示并以非零状态退出。"""
    try:
        out, a = run(argv, parser)
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
