# 城市地点 JSON

生成器支持任意城市，不自动地理编码或编造五行判断。先研究事实，再写 UTF-8 JSON 并通过 `--input` 生成地图。单张地图限 1–200 个地点；建议先做覆盖不同区域的 5–20 个高质量代表点。

```json
{
  "city": "伦敦",
  "subtitle": "London · 中心城区及周边",
  "summary": "用河流、绿地与城市功能认识伦敦的五行取象。",
  "reviewed_at": "2026-11-15",
  "coordinate_note": "WGS84 手工选取的代表位置，非测绘精度；点位不表示范围。",
  "places": [
    {
      "id": "bank",
      "name": "英格兰银行",
      "lat": 51.5142,
      "lon": -0.0885,
      "element": "金",
      "basis": "城市功能类比",
      "fact": "英格兰银行是英国中央银行。",
      "reading": "以货币与金融制度取金象，是现代类比，不据此推断财运。",
      "sources": [
        {"title": "Bank of England · About", "url": "https://www.bankofengland.co.uk/about"}
      ]
    }
  ]
}
```

- 顶层文字字段均必填，`reviewed_at` 为真实核对日期（ISO `YYYY-MM-DD`），不是生成器随手填写的今天日期。
- `id` 用唯一的小写字母、数字、连字符；`lat` 是纬度，`lon` 是经度，均为数字。Web Mercator 纬度须在 ±85.05112878 内，经度在 ±180 内。核对经纬顺序、正负号以及坐标系；内置地图使用北上方向。
- `element` 为 `金`、`木`、`水`、`火`、`土` 之一；`basis` 为 `地貌取象` 或 `城市功能类比`。不要把主取象当作唯一属性。
- `fact` 只写来源能支持的事实；`reading` 只写明确标识的五行解释。每条 `sources` 都需要 `title` 和 HTTPS `url`，至少一条。生成器校验格式，不会联网检验来源内容与事实是否一致，仍须人工核对。
- 原始标注文字通过安全的 JSON 嵌入与 DOM `textContent` 呈现，不支持 HTML。

默认使用 OpenStreetMap 底图。需要更换时，可增加可选字段（所有子字段都必填）：

```json
{
  "basemap": {
    "url": "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
    "attribution": "© OpenStreetMap contributors",
    "attribution_url": "https://www.openstreetmap.org/copyright",
    "max_zoom": 19
  }
}
```

URL 必须是 HTTPS XYZ 模板；署名依服务许可填写。此配置只是更换底图，不会转换原始点位坐标。不要把私密 API key 写进要公开提交的 HTML 或 JSON。
