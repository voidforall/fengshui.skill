"""为 city-wuxing-map 准备新城市的冻结源文件（联网，开发者用；skill 本身不下载数据）。

产出与伦敦、纽约示例相同的四份文件，写到 skills/city-wuxing-map/examples/sources/：
  <slug>-boundary.geojson.gz   role=city 为声明范围（若干行政区的并集），role=admin 为街道、镇等位置参照
  <slug>-functions.geojson.gz  OSM commercial/industrial/retail 用地面，arts_centre/cinema/theatre/nightclub 设施点
  <slug>-cover-2021.tif        ESA WorldCover 2021 v200 10m 分类，按多数类汇总到当地 UTM 50m
  <slug>-manifest.json         来源、快照时间、处理方式、署名、SHA256

用法：python3 tools/prepare_city_sources.py shanghai [--endpoint https://overpass.private.coffee/api/interpreter]
之后：python3 skills/city-wuxing-map/scripts/build_full_city.py --city shanghai --output skills/city-wuxing-map/examples/shanghai.json
依赖：skills/city-wuxing-map/requirements-build.txt。WorldCover 以 HTTP 区间读取（GDAL /vsicurl/），不下载整幅。
"""

from __future__ import annotations

import argparse
import datetime as _dt
import gzip
import hashlib
import json
import os
import time
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np
import rasterio
from pyproj import Transformer
from rasterio.enums import Resampling
from rasterio.warp import reproject
from rasterio.windows import from_bounds
from shapely import make_valid, transform as geometry_transform
from shapely.geometry import LineString, Point, Polygon, mapping
from shapely.ops import polygonize, unary_union

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "skills" / "city-wuxing-map" / "examples" / "sources"
WORLDCOVER = "https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_{tile}_Map.tif"

CITIES = {
    "shanghai": {
        "city": "上海",
        "epsg": 32651,
        "search_bbox": [120.8, 30.6, 122.25, 31.95],   # 西 南 东 北：覆盖上海全市，只用来按框检索区界
        "scope_level": "6",
        "scope_names": ["黄浦区", "徐汇区", "长宁区", "静安区", "普陀区", "虹口区", "杨浦区", "浦东新区"],
        "admin_level": "8",
        "scope_name": "上海主城区陆域（中心城区七区与浦东新区）",
        "scope_label": "主城区",
        "function_basis": "OSM用地及设施（国内用地标注覆盖不均）",
        "focus": [121.4737, 31.2304],
        "worldcover_tiles": ["N30E120"],
        "search": {"country_code": "cn", "placeholder": "人民广场 / 陆家嘴 / 31.23,121.47",
                   "hint": "中文地名或地址；也可输入纬度,经度。只显示范围内的候选。"},
    },
}


CACHE = None   # 原始 Overpass 回应的缓存目录（--cache），重跑时不必再请求


def overpass(endpoint: str, query: str, attempts: int = 5) -> dict:
    """公共 Overpass 实例常因负载断开连接或返回错误页：失败时退避重试，非 JSON 一律视为失败。"""
    key = hashlib.sha256((endpoint + query).encode()).hexdigest()[:16]
    if CACHE and (CACHE / f"{key}.json").exists():
        return json.loads((CACHE / f"{key}.json").read_text(encoding="utf-8"))
    data = urllib.parse.urlencode({"data": query}).encode()
    last = None
    for k in range(attempts):
        try:
            req = urllib.request.Request(endpoint, data=data, headers={"User-Agent": "fengshui-skill-city-map/1.0"})
            with urllib.request.urlopen(req, timeout=300) as r:
                body = r.read().decode("utf-8")
            result = json.loads(body)
            if result.get("remark", "").startswith("runtime error"):
                raise RuntimeError(result["remark"])
            if CACHE:
                CACHE.mkdir(parents=True, exist_ok=True)
                (CACHE / f"{key}.json").write_text(body, encoding="utf-8")
            return result
        except Exception as e:   # noqa: BLE001 - 网络、超时、错误页都重试
            last = e
            print(f"  Overpass 第 {k + 1} 次失败：{type(e).__name__}: {str(e)[:120]}", flush=True)
            time.sleep(30 * (k + 1))
    raise SystemExit(f"Overpass 多次失败：{last}")


def relation_polygon(rel: dict):
    """由 `out geom` 的成员 way 拼出多边形：outer 环 polygonize 后减去 inner 环。"""
    lines = {"outer": [], "inner": []}
    for m in rel.get("members", []):
        if m.get("type") == "way" and m.get("geometry") and m.get("role", "outer") in ("outer", "inner", ""):
            coords = [(p["lon"], p["lat"]) for p in m["geometry"]]
            if len(coords) >= 2:
                lines["inner" if m.get("role") == "inner" else "outer"].append(LineString(coords))
    outer = unary_union(list(polygonize(unary_union(lines["outer"])))) if lines["outer"] else None
    if outer is None or outer.is_empty:
        return None
    if lines["inner"]:
        inner = unary_union(list(polygonize(unary_union(lines["inner"]))))
        outer = outer.difference(inner)
    return make_valid(outer)


def way_polygon(el: dict):
    coords = [(p["lon"], p["lat"]) for p in el.get("geometry", [])]
    if len(coords) < 4 or coords[0] != coords[-1]:
        return None
    return make_valid(Polygon(coords))


def fetch_boundaries(cfg: dict, endpoint: str):
    """声明范围 = 各区内街道、镇界（admin_level 8）的并集。

    OSM 的区界可能含海域（如浦东新区）或外省飞地（如静安区在江苏大丰的一块），
    以街道、镇界之和为陆域范围，把这些部分排除并记入 manifest。
    """
    names = "|".join(cfg["scope_names"])
    w, so, e, n = cfg["search_bbox"]
    d = overpass(endpoint, f"""[out:json][timeout:240][bbox:{so},{w},{n},{e}];
rel["boundary"="administrative"]["admin_level"="{cfg['scope_level']}"]["name"~"^({names})$"];
out geom;""")
    districts = {}
    for el in d["elements"]:
        poly = relation_polygon(el)
        if poly is not None:
            districts[el["tags"]["name"]] = (el["id"], poly)
    missing = set(cfg["scope_names"]) - set(districts)
    if missing:
        raise SystemExit(f"OSM 中找不到区界：{'、'.join(sorted(missing))}")
    district_union = unary_union([p for _, p in districts.values()])
    d2 = overpass(endpoint, f"""[out:json][timeout:240][bbox:{so},{w},{n},{e}];
rel["boundary"="administrative"]["admin_level"="{cfg['admin_level']}"];
out geom;""")
    admins = []
    for el in d2["elements"]:
        poly = relation_polygon(el)
        if poly is None:
            continue
        rp = poly.representative_point()
        district = next((n for n, (_, p) in districts.items() if p.covers(rp)), None)
        if district is None:
            continue
        admins.append((f"{district}{el['tags'].get('name', '')}", make_valid(poly.intersection(district_union))))
    scope = make_valid(unary_union([p for _, p in admins]))
    fwd = Transformer.from_crs(4326, cfg["epsg"], always_xy=True)
    km2 = lambda g: geometry_transform(g, fwd.transform, interleaved=False).area / 1e6   # noqa: E731
    stats = {"district_relations": {n: i for n, (i, _) in districts.items()},
             "district_union_km2": round(km2(district_union), 1), "scope_km2": round(km2(scope), 1),
             "excluded_km2": round(km2(district_union.difference(scope)), 1), "admin_units": len(admins)}
    return d2.get("osm3s", {}).get("timestamp_osm_base", ""), stats, scope, admins


def fetch_functions(scope, endpoint: str, epsg: int, split: int = 2):
    """按 split×split 个子框分别查询（单次查询小，公共实例不易断开），按 OSM 类型与编号去重。"""
    minx, miny, maxx, maxy = scope.bounds
    elements, stamp = {}, ""
    for i in range(split):
        for j in range(split):
            x0, x1 = minx + (maxx - minx) * i / split, minx + (maxx - minx) * (i + 1) / split
            y0, y1 = miny + (maxy - miny) * j / split, miny + (maxy - miny) * (j + 1) / split
            q = f"""[out:json][timeout:240][bbox:{y0},{x0},{y1},{x1}];
(way["landuse"~"^(commercial|industrial|retail)$"];
 relation["landuse"~"^(commercial|industrial|retail)$"]["type"="multipolygon"];);
out geom;
(node["amenity"~"^(arts_centre|cinema|theatre|nightclub)$"];
 way["amenity"~"^(arts_centre|cinema|theatre|nightclub)$"];
 relation["amenity"~"^(arts_centre|cinema|theatre|nightclub)$"];);
out center tags;"""
            part = overpass(endpoint, q)
            stamp = stamp or part.get("osm3s", {}).get("timestamp_osm_base", "")
            print(f"  功能数据子框 {i * split + j + 1}/{split * split}：{len(part['elements'])} 项", flush=True)
            for el in part["elements"]:
                elements[(el["type"], el["id"])] = el
    d = {"elements": list(elements.values()), "osm3s": {"timestamp_osm_base": stamp}}
    fwd = Transformer.from_crs(4326, epsg, always_xy=True)
    inv = Transformer.from_crs(epsg, 4326, always_xy=True)
    local_scope = geometry_transform(scope, fwd.transform, interleaved=False)
    feats, stats = [], {"retained_features": 0, "repaired_landuse_features": 0, "skipped_unusable_features": 0,
                        "outside_scope_features": 0, "simplification_m": 2}
    for el in d["elements"]:
        tags = el.get("tags", {})
        props = {"osm_type": el["type"], "osm_id": el["id"]}
        if tags.get("name"):
            props["name"] = tags["name"]
        if "landuse" in tags and "amenity" not in tags:
            poly = relation_polygon(el) if el["type"] == "relation" else way_polygon(el)
            if poly is None or poly.is_empty:
                stats["skipped_unusable_features"] += 1
                continue
            local = geometry_transform(poly, fwd.transform, interleaved=False)
            if not local.is_valid:
                local = make_valid(local)
                stats["repaired_landuse_features"] += 1
            local = local.intersection(local_scope).simplify(2, preserve_topology=True)
            local = unary_union([g for g in getattr(local, "geoms", [local]) if g.geom_type in ("Polygon", "MultiPolygon")])
            if local.is_empty or local.area < 1:
                stats["outside_scope_features"] += 1
                continue
            geom = geometry_transform(local, inv.transform, interleaved=False)
            feats.append({"type": "Feature", "properties": {"kind": tags["landuse"], **props}, "geometry": mapping(geom)})
        else:
            if el["type"] == "node":
                pt = Point(el["lon"], el["lat"])
            elif el.get("center"):
                pt = Point(el["center"]["lon"], el["center"]["lat"])
            else:
                stats["skipped_unusable_features"] += 1
                continue
            if not scope.covers(pt):
                stats["outside_scope_features"] += 1
                continue
            props["amenity"] = tags.get("amenity", "")
            feats.append({"type": "Feature", "properties": {"kind": "culture", **props}, "geometry": mapping(pt)})
    stats["retained_features"] = len(feats)
    return d.get("osm3s", {}).get("timestamp_osm_base", ""), [minx, miny, maxx, maxy], feats, stats


def landcover(scope, epsg: int, tiles: list[str], path: Path):
    fwd = Transformer.from_crs(4326, epsg, always_xy=True)
    local = geometry_transform(scope, fwd.transform, interleaved=False)
    minx, miny, maxx, maxy = local.bounds
    minx, miny = (np.floor(np.array([minx, miny]) / 50) * 50 - 100).tolist()
    maxx, maxy = (np.ceil(np.array([maxx, maxy]) / 50) * 50 + 100).tolist()
    width, height = int((maxx - minx) / 50), int((maxy - miny) / 50)
    dst_transform = rasterio.transform.from_origin(minx, maxy, 50, 50)
    out = np.zeros((height, width), dtype=np.uint8)
    lon0, lat0, lon1, lat1 = scope.bounds
    os.environ.setdefault("GDAL_DISABLE_READDIR_ON_OPEN", "EMPTY_DIR")
    os.environ.setdefault("CURL_CA_BUNDLE", os.environ.get("SSL_CERT_FILE", "/etc/ssl/certs/ca-certificates.crt"))
    for tile in tiles:
        with rasterio.open("/vsicurl/" + WORLDCOVER.format(tile=tile)) as src:
            win = from_bounds(lon0 - 0.02, lat0 - 0.02, lon1 + 0.02, lat1 + 0.02, src.transform).round_offsets().round_lengths()
            arr = src.read(1, window=win)
            part = np.zeros_like(out)
            reproject(arr, part, src_transform=src.window_transform(win), src_crs=src.crs, src_nodata=0,
                      dst_transform=dst_transform, dst_crs=f"EPSG:{epsg}", dst_nodata=0, resampling=Resampling.mode)
            out = np.where(out == 0, part, out)
    with rasterio.open(path, "w", driver="GTiff", width=width, height=height, count=1, dtype="uint8",
                       crs=f"EPSG:{epsg}", transform=dst_transform, nodata=0, compress="deflate") as dst:
        dst.write(out, 1)
    return [WORLDCOVER.format(tile=t) for t in tiles]


def write_gz(path: Path, obj):
    # 固定 mtime，使同样内容得到同样的哈希
    with open(path, "wb") as raw, gzip.GzipFile(fileobj=raw, mode="wb", mtime=0) as f:
        f.write(json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("city", choices=sorted(CITIES))
    ap.add_argument("--endpoint", default="https://overpass.private.coffee/api/interpreter")
    ap.add_argument("--cache", type=Path, help="缓存原始 Overpass 回应的目录（重跑时复用）")
    a = ap.parse_args()
    global CACHE
    CACHE = a.cache
    cfg, slug = CITIES[a.city], a.city
    OUT.mkdir(parents=True, exist_ok=True)

    print("取区界……", flush=True)
    b_time, bstats, scope, admins = fetch_boundaries(cfg, a.endpoint)
    print(f"  {bstats}", flush=True)
    boundary = {"type": "FeatureCollection", "features":
                [{"type": "Feature", "properties": {"role": "city", "name": cfg["city"]}, "geometry": mapping(scope)}]
                + [{"type": "Feature", "properties": {"role": "admin", "name": n}, "geometry": mapping(p)} for n, p in admins]}
    write_gz(OUT / f"{slug}-boundary.geojson.gz", boundary)

    print("取功能数据……", flush=True)
    f_time, bbox, feats, stats = fetch_functions(scope, a.endpoint, cfg["epsg"])
    print("取土地覆盖……", flush=True)
    write_gz(OUT / f"{slug}-functions.geojson.gz", {"type": "FeatureCollection", "features": feats})

    tiles = landcover(scope, cfg["epsg"], cfg["worldcover_tiles"], OUT / f"{slug}-cover-2021.tif")

    files = {}
    for name in (f"{slug}-boundary.geojson.gz", f"{slug}-cover-2021.tif", f"{slug}-functions.geojson.gz"):
        data = (OUT / name).read_bytes()
        files[name] = {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}
    rel_links = "、".join(f"{n} relation/{i}" for n, i in bstats["district_relations"].items())
    manifest = {
        "city": cfg["city"], "slug": slug, "epsg": cfg["epsg"],
        "boundary_source": "https://www.openstreetmap.org/copyright",
        "boundary_note": (f"范围为 {'、'.join(cfg['scope_names'])} 内各街道、镇界（OSM admin_level={cfg['admin_level']}）之并集，"
                          f"共 {bstats['scope_km2']} km²；区界（{rel_links}）之并集为 {bstats['district_union_km2']} km²，"
                          f"其中 {bstats['excluded_km2']} km² 为区界所含海域及外省飞地，不纳入。快照 {b_time}。"),
        "boundary_stats": bstats,
        "landcover_year": 2021, "landcover_source": "https://esa-worldcover.org/en/data-access", "landcover_tiles": tiles,
        "landcover_processing": "10 m WorldCover 2021 v200 classes aggregated by majority (mode) to 50 m in local UTM; no class interpolation.",
        "osm_source": "https://www.openstreetmap.org/copyright", "osm_endpoint": a.endpoint, "osm_timestamp": f_time,
        "osm_query_bbox": bbox, "osm_normalization": stats,
        "attribution": ["© ESA WorldCover project 2021 / Contains modified Copernicus Sentinel data (2021) processed by ESA WorldCover consortium",
                        "© OpenStreetMap contributors · ODbL 1.0"],
        "files": files, "prepared_at": _dt.date.today().isoformat(),
        "scope_name": cfg["scope_name"], "focus": cfg["focus"], "search": cfg["search"],
        "function_basis": cfg.get("function_basis", "OSM用地及设施"),
        "scope_label": cfg.get("scope_label"),
    }
    (OUT / f"{slug}-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"boundary": bstats, "functions": stats, "files": files}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
