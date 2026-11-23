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
import sys
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
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
    if "scope_label" in data and not (isinstance(data["scope_label"], str) and 1 <= len(data["scope_label"]) <= 8):
        raise ValueError("scope_label 应为 1–8 字的范围简称，如「主城区」")
    if "en" in data:
        en = data["en"]
        if not isinstance(en, dict) or not isinstance(en.get("city"), str) or not en["city"].strip():
            raise ValueError("en 应为对象并含英文城市名 en.city")
        for key in ("scope_label", "scope_name"):
            if key in en:
                text(en[key], "en." + key)
        names = en.get("admin_names", {})
        if not isinstance(names, dict) or not all(isinstance(k, str) and isinstance(v, str) and v.strip() for k, v in names.items()):
            raise ValueError("en.admin_names 应为 {中文地名: 英文地名}")
        if not isinstance(en.get("search", {}), dict):
            raise ValueError("en.search 应为对象")
    if data.get("lang", "zh") not in ("zh", "en"):
        raise ValueError("lang 应为 zh 或 en（en 表示数据文字已用英文书写）")
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
        if not isinstance(analyses, dict) or not {"landscape", "function"} <= set(analyses) <= {"landscape", "function", "relative"}:
            raise ValueError(f"{label}.analyses 全城数据的每个单元必须同时提供 landscape 和 function 分析（可另有 relative）")
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


# --- 英文页面 ------------------------------------------------------------------------
# 单元的分析文字由 city_model 按同一规则重新生成英文版（判定结果须与数据一致）；
# 城市名、范围名、街道名等专名取自数据里的 en 对象（由源快照 manifest 的 en 字段带入）。

CJK = re.compile(r"[\u3400-\u9fff]")
SOURCE_EN = [
    (re.compile(r"^ESA WorldCover 2021 v200 · 土地覆盖与许可$"), "ESA WorldCover 2021 v200 · land cover and licence"),
    (re.compile(r"^OpenStreetMap用地及设施 · (.+)$"), r"OpenStreetMap land use and amenities · \1"),
    (re.compile(r"^NYC DCP规划分区＋已核对演艺区研究 · (.+)$"), r"NYC DCP zoning + checked performing-arts district study · \1"),
    (re.compile(r"^Times Square Alliance · 已研究的演艺街区范围（人工概化）$"), "Times Square Alliance · studied performing-arts district extent (hand-generalised)"),
    (re.compile(r"^《尚书·洪范》五行（维基文库）$"), "Hong Fan 洪范, Book of History (Shang Shu 尚书): the Five Elements (Wikisource)"),
    (re.compile(r"^《五行大义》卷一「辨体性」（维基文库）$"), "Wu Xing Da Yi 五行大义, vol. 1, on body and nature (Wikisource)"),
    (re.compile(r"^城市边界原始资料$"), "City boundary source"),
    (re.compile(r"^城市范围原始边界$"), "City boundary source"),
    (re.compile(r"^OSM原始对象$"), "OSM source object"),
]


def source_en(item):
    for pattern, repl in SOURCE_EN:
        if pattern.match(item["title"]):
            return dict(item, title=pattern.sub(repl, item["title"]))
    if CJK.search(item["title"]):
        raise ValueError(f"来源标题缺少英文：{item['title']}（在 generate.py 的 SOURCE_EN 补一条）")
    return item


def english(data):
    """把 schema 3 数据转成英文页面数据；数据里的排盘结论不变。"""
    from city_model import MODEL_VERSION, analyse, relative_analyses
    if data.get("lang") == "en":            # 作者已用英文写好的数据，原样使用
        return data
    en = data.get("en")
    if not isinstance(en, dict) or not isinstance(en.get("city"), str) or CJK.search(en["city"]):
        raise ValueError("英文页面需要数据里的 en.city（英文城市名）；自写数据可改为直接用英文书写并加 \"lang\": \"en\"")
    if data.get("model", {}).get("version") != MODEL_VERSION or not all("metrics" in r for r in data["regions"]):
        raise ValueError(f"英文页面要按 {MODEL_VERSION} 由 metrics 重新生成单元文字；本数据不能重算，请直接用英文书写并加 \"lang\": \"en\"")
    admin_names = en.get("admin_names", {})
    scope = en.get("scope_label")
    out = dict(data, lang="en", city=en["city"])
    out.pop("en")
    if scope:
        out["scope_label"] = scope
    cell = data["coverage"].get("cell_size_m", 1000)
    snapshot = data.get("model", {}).get("function_snapshot", "")
    n = len(data["regions"])
    out["subtitle"] = f"{scope or 'Whole city'}, covered continuously · {cell} m cells · main and secondary element with confidence notes"
    out["summary"] = (f"All {n} cells inside the {'declared area' if scope else 'city boundary'} are analysed. Tap any cell for its cover "
                      "statistics, function evidence, main and secondary element and confidence; you can also enter latitude,longitude.")
    out["coordinate_note"] = ("WGS84 coordinates. The statistical grid is clipped to the real boundary; district lines are not five-element "
                              f"boundaries. Land cover is the 2021 classification and the function data a snapshot from {snapshot}; "
                              "the classification is a modern interpretation under explicit rules.")
    out["coverage"] = dict(data["coverage"], name=en.get("scope_name") or data["coverage"]["name"],
                           sources=[source_en(x) for x in data["coverage"]["sources"]])
    if "search" in data:
        out["search"] = {**data["search"], **en.get("search", {})}
    metrics = [r["metrics"] for r in data["regions"]]
    relative = relative_analyses(metrics, "this area", "en")
    regions = []
    for r, rel in zip(data["regions"], relative):
        m = re.fullmatch(r"(.+) · 单元(\d+)", r["name"])
        admin = m.group(1) if m else r["name"]
        admin_en = admin_names.get(admin, admin)
        if CJK.search(admin_en):
            raise ValueError(f"缺少地名英文：{admin}（在源快照 manifest 的 en.admin_names 补上）")
        texts = {"landscape": analyse(r["metrics"], "landscape", "en"), "function": analyse(r["metrics"], "function", "en"),
                 "relative": rel}
        analyses = {}
        for method, a in r["analyses"].items():
            t = texts[method]
            if (t["primary"], t["secondary"], t["confidence"]) != (a["primary"], a["secondary"], a["confidence"]):
                raise ValueError(f"单元 {r['id']} 的 {method} 结论与模型重算不一致：请先用 build_full_city.py 重建数据")
            analyses[method] = dict(t, sources=[source_en(x) for x in a["sources"]])
        b = re.fullmatch(r"(\d+)米UTM连续统计格网与真实城市边界相交；本单元属于(.+)周边，行政名称仅作位置参照。格网线不是五行影响的硬边界。",
                         r["boundary"]["description"])
        desc = (f"A {b.group(1)} m UTM continuous statistical grid intersected with the real boundary; this cell lies around "
                f"{admin_names.get(b.group(2), b.group(2))}, and the district name is only a location reference. Grid lines are not "
                "hard boundaries of five-element influence." if b else r["boundary"]["description"])
        evidence = [dict(p, name="performing-arts venue" if p["name"] == "演艺设施" else p["name"],
                         note="One piece of function evidence recorded in OSM; no circle of influence is drawn around it."
                         if p["note"] == "OSM收录的区域功能证据之一；没有以该点为中心画影响圆。" else p["note"],
                         sources=[source_en(x) for x in p["sources"]]) for p in r.get("evidence", [])]
        regions.append(dict(r, name=f"{admin_en} · cell {m.group(2)}" if m else admin_en,
                            boundary=dict(r["boundary"], description=desc, sources=[source_en(x) for x in r["boundary"]["sources"]]),
                            analyses=analyses, evidence=evidence))
    out["regions"] = regions
    return out


LANGS = ("zh", "en")


def render(data, lang="zh"):
    validate(data)
    if lang not in LANGS:
        raise ValueError("lang 应为 zh 或 en")
    page = english(data) if lang == "en" else data
    payload = dict(page, basemap=data.get("basemap", DEFAULT_BASEMAP), coverage_report=validate_coverage(data))
    payload.pop("en", None)
    # Escaping '<' also prevents an annotation from closing the JSON script tag.
    embedded = json.dumps(payload, ensure_ascii=False, allow_nan=False).replace("<", "\\u003c")
    title = page["city"] + (" · Five Elements Map" if lang == "en" else " · 城市五行风水地图")
    replacements = {
        "__LANG__": "en" if lang == "en" else "zh-Hans",
        "__TITLE__": html.escape(title),
        "__DATA__": embedded,
        "__LEAFLET_CSS__": (ROOT / "assets/vendor/leaflet.css").read_text(encoding="utf-8"),
        "__SEARCH_JS__": (ROOT / "assets/search.js").read_text(encoding="utf-8"),
        "__LEAFLET_JS__": (ROOT / "assets/vendor/leaflet.js").read_text(encoding="utf-8"),
        "__LICENSE__": (ROOT / "assets/vendor/LEAFLET-LICENSE").read_text(encoding="utf-8"),
    }
    template = (ROOT / "assets/map.html").read_text(encoding="utf-8")
    return re.sub(r"__(?:LANG|TITLE|DATA|LEAFLET_CSS|LEAFLET_JS|SEARCH_JS|LICENSE)__",
                  lambda match: replacements[match.group()], template)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--example", choices=("london", "new-york", "shanghai"))
    group.add_argument("--input", type=Path, help="任意城市的区域 GeoJSON 几何与分析 JSON")
    parser.add_argument("--output", type=Path, required=True, help="输出单个 HTML 文件")
    parser.add_argument("--lang", choices=LANGS, default="zh", help="页面语言：zh 中文（默认）/ en 英文")
    args = parser.parse_args()
    source = ROOT / "examples" / (args.example + ".json") if args.example else args.input
    try:
        data = json.loads(source.read_text(encoding="utf-8"))
        result = render(data, args.lang)
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
