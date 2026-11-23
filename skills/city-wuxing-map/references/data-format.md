# 全城数据格式（schema_version: 3）

权威完整实例为 `examples/london.json` 和 `examples/new-york.json`；字段校验见 `scripts/generate.py`。不再接受旧版点位或零散片区输入。

- 顶层必填：`schema_version: 3`、非空 `city/subtitle/summary/coordinate_note`、实际核对日期 `reviewed_at`（YYYY-MM-DD）、`regions`。
- `coverage` 必填：`kind: "full-city"`、`name`、完整城市 `geometry` 和 `sources`；可选 `focus: [经度,纬度]` 为初始选中位置。
- 可选顶层 `scope_label`（1–8 字，默认「全城」）：声明范围不是整个行政市域时（如「主城区」），页面标题与口径说明用它代替「全城」；`coverage.name` 须写明具体范围。
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

## 当地地址搜索

可选顶层 `search` 对象，国家代码使用小写ISO两位代码；不设置则保留多语言地址/邮编查询，并按完整城市范围筛选结果：

```json
{"search":{"country_code":"gb","placeholder":"SW1A 1AA / SW1 / Camden","hint":"支持英国完整邮编、邮区和地址。","photon_url":"https://photon.komoot.io/api/"}}
```

`placeholder` 与 `hint` 必须按本地常用格式编写，不能照搬伦敦。纽约示例使用us和ZIP Code；法国可用fr和75001，日本可用jp和当地地址/邮编。邮编作为文字保留前导零；不要求所有国家都具有邮编。英国专用查询支持完整邮编、outcode和细分邮区候选；其他文字走Photon搜索，城市边界内的候选才可选。邮区/地区中心点仅定位该点所在单元，不代表整个邮区属性或精确邮区边界。

仅点击定位或回车发起联网请求，输入时只做本地筛选。取消过时请求、15秒超时、页面内缓存；服务失败时保留本地搜索和坐标定位。请求词发送到Postcodes.io（英国邮编）或配置的Photon实例（其他查询）；页面明确显示服务来源。

默认Photon公共实例仅供适量交互使用，无可用性保证，生产流量应配置自托管/获授权实例，并确保CORS；[使用说明](https://github.com/komoot/photon#demo-server)。[英国查询文档](https://postcodes.io/docs/overview/)。不使用公共Nominatim作通用地址服务。
