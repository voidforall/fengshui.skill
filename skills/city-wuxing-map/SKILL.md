---
name: city-wuxing-map
description: 生成覆盖完整城市范围的五行着色地图，每个统计单元都有主象、兼象、置信等级和分析原因。用于伦敦、纽约或任意城市的区域取象；默认相对取象（看各单元在范围内相对最突出的一行，依《洪范》《五行大义》以土为底色），另有综合与土地覆盖口径；地标仅作证据，不用于单宅飞星排盘。
license: MIT
metadata:
  version: "1.0.0"
---

# 城市全域五行地图

交付完整城市边界内连续着色的真实地图。用户只给城市名时，以明确的完整城市范围为默认，不能拿几个代表地标或市中心孤立片区充当全城。每个单元都应有分析，证据不足通过低置信等级表达。

## 范围、数据与解释

1. 明确城市、国家和完整范围；同名城市先确认国家。取得有来源的真实城市边界，保留版本、许可和坐标系。无法取得完整数据时说明限制，不能把空白地区称为已分析。
2. 读 [分析方法](references/method.md)。传统形体取象与现代土地覆盖/功能类比要区分；每处都能建立解释模型，不代表存在客观唯一、可测量的固有五行。
3. 取得全域土地覆盖和有来源的功能数据，优先政府与公开地图。时间、分辨率、规划用途和现状用途的区别必须明确。不得从一个银行、剧院外推整个行政区。
4. 用连续统计单元或可靠景观分区完整划分范围。内置示例采用本地UTM的1km格网裁切城市边界，不把格网冒称天然风水界线。每单元给出相对、综合、土地覆盖三种口径的主象、兼象、事实、理由、置信等级及局限，默认相对取象。
5. 按城市/国家配置当地搜索（`search.country_code`、提示及示例），例如伦敦英国邮编/邮区、纽约ZIP Code；其他国家支持当地文字地址。不要把英国格式硬套到所有城市。邮区中心点定位须区别于整区边界；联机请求仅在提交时发送，服务与生产部署限制见数据格式。
6. 按 [数据格式](references/data-format.md) 编写 schema 3 JSON。生成器用GEOS实际检验漏区、越界、重叠和标签位置；不能靠手填“100%”通过。

## 生成与交付

以下命令在本skill目录运行，实际使用时用安装目录的绝对路径，输出写到用户工作目录：

```bash
python3 -m pip install -r requirements.txt
python3 scripts/generate.py --example london --output 伦敦全城五行地图.html
python3 scripts/generate.py --example new-york --output 纽约全城五行地图.html
python3 scripts/generate.py --example shanghai --output 上海主城区五行地图.html
python3 scripts/generate.py --input 城市全域.json --output 城市全城五行地图.html
```

- HTML内嵌Leaflet和资料，无需npm或API key；地图瓦片需要联网和HTTP。在输出目录运行 `python3 -m http.server 8000 --bind 127.0.0.1`，已有服务则复用。双击文件会显示启动服务提示。
- 浏览器检查全域边缘、岛屿与水域、当地邮编/地址搜索、点击和坐标定位、三种口径、筛选、证据开关、手机布局与来源署名。不能只看渲染是否成功，不批量下载地图瓦片。
- 交付地图和JSON链接，说明范围、数据年份、统计尺度、现代解释性质和不确定性；本地链接必须有运行中的服务。

## 内置示例与重建

- 伦敦：大伦敦完整范围，1,735个单元；2021年WorldCover土地覆盖与2026-11-15 OSM功能快照。
- 纽约：五区完整范围（含行政水域），1,323个单元；同年土地覆盖、2026-11-15取得的DCP规划分区及演艺区研究。规划许可用途不等于当前营业用途。
- 上海：主城区陆域（中心城区七区与浦东新区，以OSM街道、镇界之和为准，不含区界所含海域及外省飞地），1,857个单元；同年土地覆盖与OSM功能快照（2026-07-15）。国内OSM用地标注覆盖不均，功能信号偏弱，土为主的单元较多。
- 范围不是整个行政市域时，用 `scope_label`（如「主城区」）并在 `coverage.name` 写明，不能称为全城。

已冻结源文件和SHA256在 `examples/sources/`。从这些源重新统计分析，无需联网：

```bash
python3 -m pip install -r requirements-build.txt
python3 scripts/build_full_city.py --city london --output examples/london.json
python3 scripts/build_full_city.py --city new-york --output examples/new-york.json
python3 scripts/build_full_city.py --city shanghai --output examples/shanghai.json
```

再运行生成器更新HTML。新城市应提供同格式的来源清单、完整边界、50m分类栅格及功能几何；脚本不自动虚构来源，也不自动下载新城市。更改格网尺度会改变局部结论，应重新核验。
