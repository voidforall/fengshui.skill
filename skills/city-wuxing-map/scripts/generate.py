#!/usr/bin/env python3
"""Validate full-city topology with Shapely and render a standalone interactive map."""

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
    if not isinstance(value, (list, tuple)) or len(value) != 2:
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
    if not isinstance(polygons, (list, tuple)) or not polygons:
        raise ValueError(f"{label} 缺少面坐标")
    for polygon in polygons:
        if not isinstance(polygon, (list, tuple)) or not polygon:
            raise ValueError(f"{label} 缺少环")
        for ring in polygon:
            if not isinstance(ring, (list, tuple)) or not 4 <= len(ring) <= 20000:
                raise ValueError(f"{label} 环须有 4–20000 个闭合点")
            for point in ring:
                position(point, label)
            if ring[0] != ring[-1] or len(set(map(tuple, ring))) < 3:
                raise ValueError(f"{label} 环须闭合且至少三个不同顶点")


def validate(data):
    """Validate regional inputs before writing output; never infer boundaries from points."""
    if not isinstance(data, dict) or type(data.get("schema_version")) is not int or data.get("schema_version") != 3:
        raise ValueError("需要 schema_version: 3 全城数据；旧 places 或局部片区须补充完整城市范围和连续分区")
    for key in ("city", "subtitle", "summary", "coordinate_note", "reviewed_at"):
        text(data.get(key), key)
    datetime.date.fromisoformat(data["reviewed_at"])
    regions = data.get("regions")
    if not isinstance(regions, list) or not 1 <= len(regions) <= 5000:
        raise ValueError("regions 应包含 1–5000 个片区")
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
        if not isinstance(boundary, dict) or boundary.get("kind") not in ("官方边界", "解释性概化", "统计分区"):
            raise ValueError(f"{label}.boundary.kind 应为官方边界、解释性概化或统计分区")
        text(boundary.get("description"), label + ".boundary.description")
        sources(boundary.get("sources"), label + ".boundary.sources")
        analyses = region.get("analyses")
        if not isinstance(analyses, dict) or set(analyses) != {"landscape", "function"}:
            raise ValueError(f"{label}.analyses 全城数据的每个单元必须同时提供 landscape 和 function 分析")
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
            if analysis.get("confidence") not in ("低", "中", "高"):
                raise ValueError(f"{label}.{method}.confidence 须为低、中或高")
            for key in ("reason", "limitations", "confidence_reason"):
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
    search = data.get("search", {})
    if not isinstance(search, dict):
        raise ValueError("search 应为对象")
    if "country_code" in search and not re.fullmatch(r"[a-z]{2}", str(search["country_code"])):
        raise ValueError("search.country_code 应为小写两位国家代码")
    for key in ("placeholder", "hint"):
        if key in search:
            text(search[key], "search." + key)
    if "photon_url" in search:
        https(search["photon_url"], "search.photon_url")
    validate_coverage(data)
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


def validate_coverage(data):
    """Prove complete coverage and non-overlap with GEOS, not a reported percentage."""
    try:
        from shapely.geometry import shape
        from shapely.ops import unary_union
    except ImportError as exc:
        raise ValueError("全城覆盖校验需要 Shapely：pip install -r skills/city-wuxing-map/requirements.txt") from exc
    coverage = data.get("coverage")
    if not isinstance(coverage, dict) or coverage.get("kind") != "full-city":
        raise ValueError("必须声明真实城市 coverage 范围，不接受零散片区充当全城地图")
    text(coverage.get("name"), "coverage.name")
    sources(coverage.get("sources"), "coverage.sources")
    geometry(coverage.get("geometry"), "coverage.geometry")
    scope = shape(coverage["geometry"])
    if scope.is_empty or not scope.is_valid or scope.area <= 0:
        raise ValueError("城市范围几何无效")
    polygons=[]
    for region in data["regions"]:
        polygon=shape(region["geometry"])
        if not polygon.is_valid or polygon.is_empty:
            raise ValueError(f"片区几何无效：{region['id']}")
        if not polygon.covers(shape({"type":"Point","coordinates":region["label_position"]})):
            raise ValueError(f"片区标签不在本区内：{region['id']}")
        polygons.append(polygon)
    union=unary_union(polygons)
    tolerance=max(scope.area*1e-9, 1e-12)
    missing=scope.difference(union).area
    outside=union.difference(scope).area
    overlap=max(0,sum(p.area for p in polygons)-union.area)
    if missing>tolerance or outside>tolerance or overlap>tolerance:
        raise ValueError(f"全城分区不完整：漏区比例 {missing/scope.area:.8%}，越界比例 {outside/scope.area:.8%}，重叠比例 {overlap/scope.area:.8%}")
    # Preserve full precision for validation above; serialize below the tolerance
    # consistently across Python/GEOS builds instead of publishing floating-point noise.
    return {"coverage_percent":round(100*(1-missing/scope.area), 8),
            "overlap_percent":round(100*overlap/scope.area, 8),
            "outside_percent":round(100*outside/scope.area, 8),"region_count":len(polygons)}


def render(data):
    validate(data)
    payload = dict(data, basemap=data.get("basemap", DEFAULT_BASEMAP), coverage_report=validate_coverage(data))
    # Escaping '<' also prevents an annotation from closing the JSON script tag.
    embedded = json.dumps(payload, ensure_ascii=False, allow_nan=False).replace("<", "\\u003c")
    replacements = {
        "__TITLE__": html.escape(data["city"] + " · 城市五行风水地图"),
        "__DATA__": embedded,
        "__LEAFLET_CSS__": (ROOT / "assets/vendor/leaflet.css").read_text(encoding="utf-8"),
        "__SEARCH_JS__": (ROOT / "assets/search.js").read_text(encoding="utf-8"),
        "__LEAFLET_JS__": (ROOT / "assets/vendor/leaflet.js").read_text(encoding="utf-8"),
        "__LICENSE__": (ROOT / "assets/vendor/LEAFLET-LICENSE").read_text(encoding="utf-8"),
    }
    template = (ROOT / "assets/map.html").read_text(encoding="utf-8")
    return re.sub(r"__(?:TITLE|DATA|LEAFLET_CSS|LEAFLET_JS|SEARCH_JS|LICENSE)__",
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
