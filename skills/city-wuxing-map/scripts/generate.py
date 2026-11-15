#!/usr/bin/env python3
"""Render researched city annotations over a real map; Python standard library only."""

from __future__ import annotations

import argparse
import datetime
import html
import json
import math
from pathlib import Path
import re
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
ELEMENTS = "金木水火土"
DEFAULT_BASEMAP = {
    "url": "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
    "attribution": "© OpenStreetMap contributors",
    "attribution_url": "https://www.openstreetmap.org/copyright",
    "max_zoom": 19,
}


def text(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} 应为非空文字")
    return value


def https(value, label):
    text(value, label)
    url = urlsplit(value)
    if url.scheme != "https" or not url.hostname or url.username or url.password:
        raise ValueError(f"{label} 应为 HTTPS URL（不含账号密码）")
    return value


def validate(data):
    """Reject unusable geographic inputs before writing any output."""
    if not isinstance(data, dict):
        raise ValueError("数据应为 JSON 对象")
    for key in ("city", "subtitle", "summary", "coordinate_note", "reviewed_at"):
        text(data.get(key), key)
    datetime.date.fromisoformat(data["reviewed_at"])
    places = data.get("places")
    if not isinstance(places, list) or not 1 <= len(places) <= 200:
        raise ValueError("places 应包含 1–200 个地点")
    seen = set()
    for i, place in enumerate(places):
        label = f"places[{i}]"
        if not isinstance(place, dict):
            raise ValueError(f"{label} 应为对象")
        for key in ("id", "name", "fact", "reading"):
            text(place.get(key), f"{label}.{key}")
        if not re.fullmatch(r"[a-z0-9-]+", place["id"]) or place["id"] in seen:
            raise ValueError(f"{label}.id 应为唯一的小写英文/数字/连字符标识")
        seen.add(place["id"])
        if place.get("element") not in list(ELEMENTS):
            raise ValueError(f"{label}.element 应为金、木、水、火、土之一")
        if place.get("basis") not in ("地貌取象", "城市功能类比"):
            raise ValueError(f"{label}.basis 应为地貌取象或城市功能类比")
        for key, limit in (("lat", 85.05112878), ("lon", 180)):
            value = place.get(key)
            if type(value) not in (int, float) or not math.isfinite(value) or abs(value) > limit:
                raise ValueError(f"{label}.{key} 超出 Web Mercator 有效范围")
        sources = place.get("sources")
        if not isinstance(sources, list) or not sources:
            raise ValueError(f"{label}.sources 至少需要一条事实来源")
        for source in sources:
            if not isinstance(source, dict):
                raise ValueError(f"{label}.sources 中每条来源应为对象")
            text(source.get("title"), f"{label}.sources.title")
            https(source.get("url"), f"{label}.sources.url")
    basemap = data.get("basemap", DEFAULT_BASEMAP)
    if not isinstance(basemap, dict):
        raise ValueError("basemap 应为对象")
    https(basemap.get("url"), "basemap.url")
    if not all(token in basemap["url"] for token in ("{z}", "{x}", "{y}")):
        raise ValueError("basemap.url 必须包含 {z}、{x}、{y}")
    text(basemap.get("attribution"), "basemap.attribution")
    https(basemap.get("attribution_url"), "basemap.attribution_url")
    if type(basemap.get("max_zoom")) is not int or not 1 <= basemap["max_zoom"] <= 22:
        raise ValueError("basemap.max_zoom 应为 1–22 的整数")
    return data


def render(data):
    validate(data)
    payload = dict(data, basemap=data.get("basemap", DEFAULT_BASEMAP))
    # Escaping '<' also prevents an annotation from closing the JSON script tag.
    embedded = json.dumps(payload, ensure_ascii=False, allow_nan=False).replace("<", "\\u003c")
    replacements = {
        "__TITLE__": html.escape(data["city"] + " · 城市五行风水地图"),
        "__DATA__": embedded,
        "__LEAFLET_CSS__": (ROOT / "assets/vendor/leaflet.css").read_text(encoding="utf-8"),
        "__LEAFLET_JS__": (ROOT / "assets/vendor/leaflet.js").read_text(encoding="utf-8"),
        "__LICENSE__": (ROOT / "assets/vendor/LEAFLET-LICENSE").read_text(encoding="utf-8"),
    }
    template = (ROOT / "assets/map.html").read_text(encoding="utf-8")
    return re.sub(r"__(?:TITLE|DATA|LEAFLET_CSS|LEAFLET_JS|LICENSE)__",
                  lambda match: replacements[match.group()], template)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--example", choices=("london", "new-york"))
    group.add_argument("--input", type=Path, help="任意城市的已核对地点 JSON")
    parser.add_argument("--output", type=Path, required=True, help="输出单个 HTML 文件")
    args = parser.parse_args()
    source = ROOT / "examples" / (args.example + ".json") if args.example else args.input
    try:
        data = json.loads(source.read_text(encoding="utf-8"))
        result = render(data)
        if args.output.resolve() == source.resolve():
            raise ValueError("输出路径不能覆盖输入数据")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(result, encoding="utf-8")
    except (OSError, ValueError) as exc:
        parser.exit(2, f"生成失败：{exc}\n")
    print(args.output.resolve())
    print("通过 HTTP 打开并联网加载真实底图；在输出目录运行：")
    print("python3 -m http.server 8000 --bind 127.0.0.1")


if __name__ == "__main__":
    main()
