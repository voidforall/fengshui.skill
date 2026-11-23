#!/usr/bin/env python3
"""Build a complete partition from a frozen city source bundle; no network requests."""
from __future__ import annotations
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import rasterio
from rasterio.features import geometry_mask
from rasterio.windows import from_bounds, Window, transform as window_transform
from pyproj import Transformer
from shapely import transform as geometry_transform, make_valid
from shapely.geometry import shape, mapping, box, Point
from shapely.ops import unary_union
from shapely.strtree import STRtree

from city_model import analyse, MODEL_VERSION

ROOT = Path(__file__).resolve().parents[1]


def project(geom, transformer):
    return geometry_transform(geom, transformer.transform, interleaved=False)


def read_gzip(path):
    with gzip.open(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def prepare_inputs(source_dir, slug):
    manifest = json.loads((source_dir / f"{slug}-manifest.json").read_text(encoding="utf-8"))
    for name, spec in manifest["files"].items():
        if hashlib.sha256((source_dir / name).read_bytes()).hexdigest() != spec["sha256"]:
            raise ValueError(f"源快照校验失败：{name}")
    boundaries = read_gzip(source_dir / f"{slug}-boundary.geojson.gz")["features"]
    scope = unary_union([shape(f["geometry"]) for f in boundaries if f["properties"].get("role") == "city"])
    admins = [(f["properties"]["name"], shape(f["geometry"])) for f in boundaries if f["properties"].get("role") == "admin"]
    functions = read_gzip(source_dir / f"{slug}-functions.geojson.gz")["features"]
    return manifest, scope, admins, functions


def raster_statistics(dataset, polygon):
    raw_window = from_bounds(*polygon.bounds, transform=dataset.transform)
    left = max(0, math.floor(raw_window.col_off))
    top = max(0, math.floor(raw_window.row_off))
    right = min(dataset.width, math.ceil(raw_window.col_off + raw_window.width))
    bottom = min(dataset.height, math.ceil(raw_window.row_off + raw_window.height))
    win = Window(left, top, max(1, right-left), max(1, bottom-top))
    arr = dataset.read(1, window=win)
    mask = geometry_mask([mapping(polygon)], transform=window_transform(win, dataset.transform),
                         out_shape=arr.shape, invert=True)
    values = arr[mask & (arr > 0)]
    sampling = "50m多数分类统计"
    if not values.size:
        point = polygon.representative_point()
        value = next(dataset.sample([(point.x, point.y)]))[0]
        if not value:
            raise ValueError("土地覆盖缺少有效样本；请补充数据，不能静默编造主象")
        values = np.array([value], dtype=np.uint8)
        sampling = "边界小单元代表点补样"
    total = len(values)
    proportions = {
        "water": float(np.isin(values, [80]).sum() / total),
        "vegetation": float(np.isin(values, [10,20,30,90,95,100]).sum() / total),
        "built": float(np.isin(values, [50]).sum() / total),
        "open": float(np.isin(values, [40,60,70]).sum() / total),
    }
    if abs(sum(proportions.values()) - 1) > 1e-8:
        raise ValueError("土地覆盖中存在未定义类别")
    return dict(proportions, sample_count=total, sampling=sampling)


def build(source_dir, slug, cell_size):
    manifest, scope, admins, features = prepare_inputs(source_dir, slug)
    forward = Transformer.from_crs(4326, manifest["epsg"], always_xy=True)
    inverse = Transformer.from_crs(manifest["epsg"], 4326, always_xy=True)
    projected_scope = project(scope, forward)
    geoms = [project(shape(f["geometry"]), forward) for f in features]
    tree = STRtree(geoms)
    names = [name for name, _ in admins]
    admin_geoms = [g for _, g in admins]
    admin_tree = STRtree(admin_geoms)
    snapshot = manifest.get("function_snapshot", manifest.get("osm_timestamp", ""))
    function_title = manifest.get("function_source_title", "OpenStreetMap用地及设施")
    function_url = manifest.get("function_source_url", manifest.get("osm_source"))
    refs = [
        {"title":"ESA WorldCover 2021 v200 · 土地覆盖与许可", "url":manifest["landcover_source"]},
        {"title":function_title + " · " + snapshot, "url":function_url},
    ] + manifest.get("extra_sources", [])
    minx,miny,maxx,maxy = projected_scope.bounds
    xs = range(math.floor(minx/cell_size)*cell_size-cell_size, math.ceil(maxx/cell_size)*cell_size+cell_size, cell_size)
    ys = range(math.floor(miny/cell_size)*cell_size-cell_size, math.ceil(maxy/cell_size)*cell_size+cell_size, cell_size)
    regions=[]
    with rasterio.open(source_dir / f"{slug}-cover-2021.tif") as dataset:
        for y in ys:
            for x in xs:
                # Inverse-project shared grid corners first, then clip in WGS84.
                # Adjacent cells therefore share exactly the same edges in output coordinates.
                quad = project(box(x,y,x+cell_size,y+cell_size), inverse)
                clipped = scope.intersection(quad)
                if clipped.is_empty or clipped.area == 0:
                    continue
                if clipped.geom_type == "GeometryCollection":
                    clipped = unary_union([g for g in clipped.geoms if g.geom_type in ("Polygon","MultiPolygon")])
                if clipped.is_empty or clipped.area == 0:
                    continue
                if not clipped.is_valid:
                    clipped = make_valid(clipped)
                local = project(clipped, forward)
                metrics = raster_statistics(dataset, local)
                metrics["area_km2"] = round(local.area / 1e6, 6)
                grouped={"commercial":[],"industrial":[],"retail":[],"culture_area":[]}
                points=[]
                for index in tree.query(local, predicate="intersects"):
                    props=features[index]["properties"]
                    if props["kind"] == "culture":
                        if local.covers(geoms[index]): points.append(index)
                    else:
                        grouped[props["kind"]].append(geoms[index].intersection(local))
                metrics["commercial_industrial"] = min(1, unary_union(grouped["commercial"]+grouped["industrial"]).area/local.area)
                metrics["retail"] = min(1, unary_union(grouped["retail"]).area/local.area)
                metrics["culture_area"] = min(1, unary_union(grouped["culture_area"]).area/local.area)
                metrics["culture_count"] = len(points)
                metrics["function_basis"] = manifest.get("function_basis", "OSM用地及设施")
                metrics = {k:round(v,6) if isinstance(v,float) else v for k,v in metrics.items()}
                label = clipped.representative_point()
                nearby = list(admin_tree.query(label, predicate="intersects"))
                admin_index = nearby[0] if nearby else admin_tree.nearest(label)
                admin = names[admin_index]
                region_id=f"cell-{x}-{y}".replace("--", "-n")
                # Numeric x/y identifiers are stable in the source UTM CRS.
                analyses={method:dict(analyse(metrics,method),sources=refs) for method in ("landscape","function")}
                evidence=[]
                for index in points[:3]:
                    props=features[index]["properties"];position=project(geoms[index],inverse)
                    evidence.append({"name":props.get("name") or props.get("amenity") or "演艺设施", "position":[position.x,position.y],
                        "note":"OSM收录的区域功能证据之一；没有以该点为中心画影响圆。", "sources":[{"title":"OSM原始对象", "url":f"https://www.openstreetmap.org/{props['osm_type']}/{props['osm_id']}"}]})
                regions.append({"id":region_id,"name":f"{admin} · 单元{len(regions)+1:04d}","geometry":mapping(clipped),
                    "label_position":[label.x,label.y],"boundary":{"kind":"统计分区","description":f"{cell_size}米UTM连续统计格网与真实城市边界相交；本单元属于{admin}周边，行政名称仅作位置参照。格网线不是五行影响的硬边界。", "sources":[{"title":"城市边界原始资料", "url":manifest["boundary_source"]}]},
                    "preferred_method":"function","analyses":analyses,"metrics":{k:round(v,6) if isinstance(v,float) else v for k,v in metrics.items()},"evidence":evidence})
    label = manifest.get("scope_label")
    extra = {"scope_label": label} if label else {}
    return {**extra, "search":manifest.get("search", {}),"schema_version":3,"city":manifest["city"],"subtitle":f"{label or '全城'}连续覆盖 · {cell_size}米分析单元 · 含主象、兼象与置信说明",
        "summary":f"{'声明范围' if label else '城市边界'}内 {len(regions)} 个单元全部纳入分析。点击任何区块查看真实覆盖统计、功能证据、主象兼象与置信说明；可输入纬度,经度定位。",
        "reviewed_at":manifest.get("prepared_at", snapshot[:10]),"coordinate_note":"WGS84坐标。统计格网裁切至真实城市边界，区界不代表五行硬边界。土地覆盖为2021年历史分类，功能资料快照为"+snapshot+"；归类属于明确规则下的现代解释。",
        "coverage":{"kind":"full-city","name":manifest.get("scope_name", "大伦敦完整范围" if slug=="london" else manifest["city"]+"完整范围"),"geometry":mapping(scope),
                    "sources":[{"title":"城市范围原始边界", "url":manifest["boundary_source"]}],"cell_size_m":cell_size,"focus":manifest.get("focus") or ([-0.1278,51.5074] if slug=="london" else [-74.006,40.7128] if slug=="new-york" else list(scope.representative_point().coords)[0])},
        "model":{"version":MODEL_VERSION,"attribution":manifest["attribution"],"source_manifest":manifest,"landcover_year":2021,"function_snapshot":snapshot,"function_dataset":function_title},
        "regions":regions}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--city',required=True,help='源快照文件名前缀，如 london / new-york；也可使用自备城市快照')
    parser.add_argument('--sources',type=Path,default=ROOT/'examples/sources')
    parser.add_argument('--cell-size',type=int,default=1000)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if not 500<=args.cell_size<=5000:parser.error('cell-size 须在500–5000米之间')
    data=build(args.sources,args.city,args.cell_size)
    from generate import validate
    validate(data)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(data,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8')
    print(f'{args.city}: {len(data["regions"])} cells; full-city partition validated; {args.output}')

if __name__=='__main__':main()
