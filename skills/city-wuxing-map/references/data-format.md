# 全城数据格式（schema_version: 3）

权威完整实例为 `examples/london.json` 和 `examples/new-york.json`；字段校验见 `scripts/generate.py`。不再接受旧版点位或零散片区输入。

- 顶层必填：`schema_version: 3`、非空 `city/subtitle/summary/coordinate_note`、实际核对日期 `reviewed_at`（YYYY-MM-DD）、`regions`。
- `coverage` 必填：`kind: "full-city"`、`name`、完整城市 `geometry` 和 `sources`；可选 `focus: [经度,纬度]` 为初始选中位置。
- `regions` 为1–5000个不重叠且覆盖完整范围的单元。每项含唯一小写字母/数字/连字符 `id`、`name`、`geometry`、在本区内部的 `label_position`。
- 几何为WGS84 GeoJSON Polygon（可有洞）或MultiPolygon。每环4–20000点、首尾闭合、有限坐标，纬度限±85.05112878、经度±180。GEOS检查有效拓扑、并集漏区/越界与面积重叠；不接受伪造的覆盖报告。
- `boundary` 含 `kind`（统计分区/官方边界/解释性概化）、`description` 与 `sources`。统计格网必须明确尺度，不能标成官方风水区。
- 每个单元 `analyses` 必须同时有 `landscape` 和 `function`。`preferred_method` 指向其中之一；全城综合视图使用该字段，内置示例均为function。
- 每份分析必填：`primary`（金木水火土之一）、`secondary`（不重复且不同于主象，可空）、`facts`（非空文字数组）、`reason`、`limitations`、`confidence`（低/中/高）、`confidence_reason`、`sources`。不能用空分析把单元漏掉；资料不足必须在理由、低置信等级中说明，无法建立有依据的分类则补数据再生成。
- 可选 `evidence` 为证据点数组，每项含 `name/position/note/sources`；证据支持整体解释，不用固定半径外推。
- 来源都是 `{ "title": "来源标题", "url": "https://…" }`，至少一条。事实来源不自动证明五行解释；所有文字按纯文字安全嵌入。
- 可选 `metrics`、`model` 保留测量输入、规则版本、来源日期和署名，离线构建器生成这些字段。`coverage_report` 由生成器实际计算，输入同名字段不会被信任。

可选底图对象 `basemap` 全部字段必填，保留服务要求的署名，不公开私密key：

```json
{"basemap":{"url":"https://tile.openstreetmap.org/{z}/{x}/{y}.png","attribution":"© OpenStreetMap contributors","attribution_url":"https://www.openstreetmap.org/copyright","max_zoom":19}}
```

XYZ地址需含三个占位符，max_zoom为1–22整数；底图配置不转换区域坐标。
