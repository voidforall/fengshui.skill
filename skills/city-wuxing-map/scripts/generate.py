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


def sources(value, label):
    if not isinstance(value, list) or not value:
        raise ValueError(f"{label} 至少需要一条来源")
    for source in value:
        if not isinstance(source, dict):
            raise ValueError(f"{label} 中每条来源应为对象")
        text(source.get("title"), label + ".title")
        https(source.get("url"), label + ".url")


def position(value, label):
    if not isinstance(value, list) or len(value) != 2:
        raise ValueError(f"{label} 应为 [经度, 纬度]")
    for number, limit in zip(value, (180, 85.05112878)):
        if type(number) not in (int, float) or not math.isfinite(number) or abs(number) > limit:
            raise ValueError(f"{label} 超出 WGS84/Web Mercator 范围")


def geometry(value, label):
    if not isinstance(value, dict) or value.get("type") not in ("Polygon", "MultiPolygon"):
        raise ValueError(f"{label} 应为 GeoJSON Polygon 或 MultiPolygon")
    polygons = value.get("coordinates")
    if value["type"] == "Polygon":
        polygons = [polygons]
    if not isinstance(polygons, list) or not polygons:
        raise ValueError(f"{label} 缺少面坐标")
    for polygon in polygons:
        if not isinstance(polygon, list) or not polygon:
            raise ValueError(f"{label} 缺少环")
        for ring in polygon:
            if not isinstance(ring, list) or not 4 <= len(ring) <= 1000:
                raise ValueError(f"{label} 环须有 4–1000 个闭合点")
            for point in ring:
                position(point, label)
            if ring[0] != ring[-1] or len(set(map(tuple, ring))) < 3:
                raise ValueError(f"{label} 环须闭合且至少三个不同顶点")
            area = sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(ring, ring[1:]))
            if abs(area) < 1e-12:
                raise ValueError(f"{label} 环面积为零或退化")


def validate(data):
    """Validate regional inputs before writing output; never infer boundaries from points."""
    if not isinstance(data, dict) or type(data.get("schema_version")) is not int or data.get("schema_version") != 2:
        raise ValueError("需要 schema_version: 2 区域数据；旧 places 点位须补充区域边界和分析，不能自动扩大成区块")
    for key in ("city", "subtitle", "summary", "coordinate_note", "reviewed_at"):
        text(data.get(key), key)
    datetime.date.fromisoformat(data["reviewed_at"])
    regions = data.get("regions")
    if not isinstance(regions, list) or not 1 <= len(regions) <= 200:
        raise ValueError("regions 应包含 1–200 个片区")
    seen = set()
    for i, region in enumerate(regions):
        label = f"regions[{i}]"
        if not isinstance(region, dict):
            raise ValueError(f"{label} 应为对象")
        for key in ("id", "name"):
            text(region.get(key), label + "." + key)
        if not re.fullmatch(r"[a-z0-9-]+", region["id"]) or region["id"] in seen:
            raise ValueError(f"{label}.id 应为唯一的小写英文/数字/连字符标识")
        seen.add(region["id"])
        geometry(region.get("geometry"), label + ".geometry")
        position(region.get("label_position"), label + ".label_position")
        boundary = region.get("boundary")
        if not isinstance(boundary, dict) or boundary.get("kind") not in ("官方边界", "解释性概化"):
            raise ValueError(f"{label}.boundary.kind 应为官方边界或解释性概化")
        text(boundary.get("description"), label + ".boundary.description")
        sources(boundary.get("sources"), label + ".boundary.sources")
        analyses = region.get("analyses")
        if not isinstance(analyses, dict) or set(analyses) - {"landscape", "function"}:
            raise ValueError(f"{label}.analyses 只接受 landscape / function（空对象表示待分析）")
        if (analyses and region.get("preferred_method") not in analyses) or (not analyses and region.get("preferred_method") is not None):
            raise ValueError(f"{label}.preferred_method 必须有对应分析")
        for method, analysis in analyses.items():
            if not isinstance(analysis, dict):
                raise ValueError(f"{label}.{method} 应为对象")
            primary = analysis.get("primary")
            secondary = analysis.get("secondary")
            if primary not in list(ELEMENTS):
                raise ValueError(f"{label}.{method}.primary 应为金木水火土之一")
            if not isinstance(secondary, list) or any(e not in list(ELEMENTS) or e == primary for e in secondary) or len(set(secondary)) != len(secondary):
                raise ValueError(f"{label}.{method}.secondary 应为不重复且不同于主象的五行列表")
            for key in ("reason", "limitations"):
                text(analysis.get(key), label + "." + method + "." + key)
            facts = analysis.get("facts")
            if not isinstance(facts, list) or not facts:
                raise ValueError(f"{label}.{method}.facts 至少需要一条区域事实")
            for fact in facts:
                text(fact, label + ".facts")
            sources(analysis.get("sources"), label + "." + method + ".sources")
        evidence = region.get("evidence", [])
        if not isinstance(evidence, list):
            raise ValueError(f"{label}.evidence 应为列表")
        for point in evidence:
            if not isinstance(point, dict):
                raise ValueError(f"{label}.evidence 应包含对象")
            for key in ("name", "note"):
                text(point.get(key), label + ".evidence." + key)
            position(point.get("position"), label + ".evidence.position")
            sources(point.get("sources"), label + ".evidence.sources")
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
    group.add_argument("--input", type=Path, help="任意城市的区域 GeoJSON 几何与分析 JSON")
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
