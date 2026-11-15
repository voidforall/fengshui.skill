# 区域数据格式（schema_version: 2）

任意城市均可输入。先研究区域整体特征、取得或概化多边形，再运行 `--input`。不要把旧版 `places` 点位自动加半径转成面；v1 输入会收到补齐区域数据的错误提示。

```json
{
  "schema_version": 2,
  "city": "示例城市",
  "subtitle": "中心城区 · 区域分析",
  "summary": "一组有依据的区域主象和兼象。",
  "reviewed_at": "2026-11-15",
  "coordinate_note": "WGS84；区界为公开地图参照下的解释性概化范围。",
  "regions": [{
    "id": "river-core",
    "name": "河谷核心观察片",
    "geometry": {"type": "Polygon", "coordinates": [[[0,51],[0.01,51],[0.01,51.01],[0,51.01],[0,51]]]},
    "label_position": [0.005,51.005],
    "boundary": {
      "kind": "解释性概化",
      "description": "说明观察范围及为什么以这些河岸或道路划界；此处坐标仅示范格式，并非真实研究结论。",
      "sources": [{"title":"公开地图参照", "url":"https://www.openstreetmap.org/#map=14/51.005/0.005"}]
    },
    "preferred_method": "landscape",
    "analyses": {
      "landscape": {
        "primary": "水",
        "secondary": ["木"],
        "facts": ["填写已核对的区域整体事实。"],
        "reason": "解释为什么水系构成片区骨架，以及植被为何构成兼象。",
        "limitations": "说明混合、过渡、资料日期与解释范围。",
        "sources": [{"title":"事实来源标题", "url":"https://www.openstreetmap.org/"}]
      }
    },
    "evidence": [{
      "name": "观察点",
      "position": [0.005,51.005],
      "note": "说明它支持哪条区域观察，不靠一个点决定整区。",
      "sources": [{"title":"观察点来源", "url":"https://www.openstreetmap.org/"}]
    }]
  }]
}
```

- 顶层文字均必填，日期为资料实际核对日。`regions` 含1–200区；`id` 为唯一的小写字母/数字/连字符标识。
- `geometry` 支持 GeoJSON `Polygon`（含内环）和 `MultiPolygon`。每环4–1000点，首尾相同，至少三个不同顶点且不退化。经度范围±180、纬度±85.05112878；两个数都必须有限。生成器不检验所有复杂拓扑，数据作者须核对自交、洞、重叠及范围。`label_position` 应选在片区内部。
- `boundary.kind` 为 `官方边界` 或 `解释性概化`。描述中写范围、年份/精度、划界依据；至少一条来源。只有实际取得官方几何时才用“官方边界”。
- `analyses` 可包含 `landscape` / `function`；`preferred_method` 必须指向已存在的分析。整区待分析时用空对象 `{}` 并令 `preferred_method` 为 `null`，综合视图也会显示灰色。缺失的方法保持待分析，不填猜测结论。
- 分析包含 `primary`（金木水火土之一）、`secondary`（不重复且不同于主象的五行数组，可空）、非空 `facts` 数组、`reason`、`limitations` 和至少一条 `sources`。事实来源不自动证明解释。
- `evidence` 可省略或为空；每点填写 `name`、`position`、`note`、`sources`。点应属于对应区域或在说明中明确其外部观察关系。
- 全部来源需 `title` 与 HTTPS `url`。文字不支持 HTML，安全嵌入后通过 DOM textContent 显示。

可选 `basemap` 替换 XYZ 服务；下列子字段均必填，署名必须符合服务许可：

```json
{"basemap":{"url":"https://tile.openstreetmap.org/{z}/{x}/{y}.png","attribution":"© OpenStreetMap contributors","attribution_url":"https://www.openstreetmap.org/copyright","max_zoom":19}}
```

URL 包含 `{z}`、`{x}`、`{y}`；`max_zoom` 为1–22整数。不要公开私密 API key。底图配置不会转换原始区域坐标。
