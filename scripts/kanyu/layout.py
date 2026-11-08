"""户型对位：把房间放到九宫方位上，给出每个房间所在宫的飞星与八宅吉凶。

纯计算，不做格式化。房间方位以宅中心立极，按八方（或宫名）指定。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .bazhai import YOUNIAN_JI, MinGua, east_west, mingua_of, younian
from .core import PALACE_DIR, fly, mountain_palace
from .feixing import Chart, palace_flags

DIR_PALACE = {d: p for p, d in PALACE_DIR.items()}          # 方位名 → 宫
ALIASES = {"正北": "北", "正南": "南", "正东": "东", "正西": "西", "中宫": "中", "中央": "中"}


def parse_palace(s: str) -> str:
    """方位名（北、东北……中）或宫名（坎、艮……中）→ 宫名。"""
    s = ALIASES.get(s.strip(), s.strip())
    if s in DIR_PALACE:
        return DIR_PALACE[s]
    if s in PALACE_DIR:
        return s
    raise ValueError(f"无法识别方位 {s!r}：请用 北/东北/东/东南/南/西南/西/西北/中 或宫名")


def parse_rooms(spec: str) -> list[tuple[str, str]]:
    """'大门=南,主卧=西北' → [('大门', '离'), ('主卧', '乾')]。同名房间不可重复。"""
    rooms, seen = [], set()
    for part in [p for p in spec.replace("，", ",").split(",") if p.strip()]:
        if "=" not in part:
            raise ValueError(f"房间格式应为 名称=方位，收到 {part!r}")
        name, where = (x.strip() for x in part.split("=", 1))
        if not name:
            raise ValueError(f"房间名为空：{part!r}")
        if name in seen:
            raise ValueError(f"房间重复：{name}")
        seen.add(name)
        rooms.append((name, parse_palace(where)))
    return rooms


@dataclass
class Member:
    label: str
    mingua: MinGua
    younian: dict[str, str]          # 宫 → 游年名


def palace_younian(gua: str) -> dict[str, str]:
    """以某卦（宅卦或命卦）论，各宫的游年名。中宫无游年。"""
    return {p: name for name, p in younian(gua).items()}


def make_member(label: str, year: int, gender: str) -> Member:
    mg = mingua_of(year, gender)
    return Member(label, mg, palace_younian(mg.gua))


@dataclass
class RoomReading:
    name: str
    palace: str
    direction: str
    shan: int
    xiang: int
    yun: int
    annual: int | None
    flags: list[str]
    house_younian: str | None                 # 以宅卦论
    house_ji: bool | None
    members: dict[str, str] = field(default_factory=dict)   # 家人称呼 → 游年名


def read_rooms(ch: Chart, rooms: list[tuple[str, str]], members: list[Member],
               annual: int | None = None) -> list[RoomReading]:
    ann = fly(annual) if annual else None
    house = palace_younian(mountain_palace(ch.sit))
    out = []
    for name, p in rooms:
        hy = house.get(p)
        out.append(RoomReading(
            name=name, palace=p, direction=PALACE_DIR[p],
            shan=ch.shan[p], xiang=ch.xiang[p], yun=ch.yunpan[p],
            annual=ann[p] if ann else None,
            flags=palace_flags(ch.shan[p], ch.xiang[p], ann[p] if ann else None),
            house_younian=hy, house_ji=(hy in YOUNIAN_JI) if hy else None,
            members={m.label: m.younian.get(p, "") for m in members},
        ))
    return out


def house_gua(ch: Chart) -> tuple[str, str]:
    g = mountain_palace(ch.sit)
    return g, east_west(g)


__all__ = ["parse_palace", "parse_rooms", "Member", "make_member", "palace_younian", "RoomReading",
           "read_rooms", "house_gua"]
