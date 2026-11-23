# 冻结的全城数据源

每个manifest记录原始来源、处理方式、日期、署名，以及每份冻结文件的SHA256与字节数。`build_full_city.py` 先核对哈希，再从这些文件重建，不访问网络。伦敦、纽约数据取得于2026-11-15，上海取得于2026-11-23（OSM快照时间见manifest）；这不表示所有事实都在该年测量。

## 文件约定

每城市三份文件：`*-boundary.geojson.gz`（FeatureCollection，role=city为完整边界，其他行政区只用于命名）、`*-cover-2021.tif`（当地UTM、50m分类栅格）、`*-functions.geojson.gz`（WGS84，kind为commercial/industrial/retail/culture_area面或culture点）。manifest的epsg指本地投影。原始10m WorldCover使用最近多数类汇总，不插值类别。

伦敦边界来自GLA公开GIS ZIP；行政区名称参照2015统计界线。功能资料来自manifest记录的Overpass全域查询，包含commercial/industrial/retail用地和arts_centre/cinema/theatre/nightclub设施；保留9759项，无法使用的5项跳过，面在UTM下修复、裁切并简化2m，非点设施用代表点。不把对象数量当作实际商家普查。

纽约使用DCP含水域五区边界的并集。功能面来自DCP ArcGIS nyzd图层：C1–C4归零售服务，C5–C6归商业，M归工业，共1435面；这是许可用途，不是现状营业统计。另一个culture_area来自已有Broadway演艺区研究的人工概化范围，单独列来源，不把它伪称官方规划面。源文件保留几何与必要的分类及来源信息。

上海范围为黄浦、徐汇、长宁、静安、普陀、虹口、杨浦七区与浦东新区内各街道、镇界（OSM admin_level=8）之并集，1,691 km²。OSM这八个区的区界之并集为5,469 km²，多出的3,778 km²是浦东新区区界所含的东海海域，以及静安区区界中位于江苏大丰的一块飞地，均不纳入；manifest的boundary_note与boundary_stats记录了区界编号和面积。功能资料取自Overpass镜像（overpass.private.coffee，数据库快照2026-07-15）分四个子框查询后去重，保留2,235项；国内OSM用地标注覆盖不均，未收录的用地不等于实际不存在。三份源文件由仓库的 `tools/prepare_city_sources.py shanghai` 生成，可复现（gzip固定时间戳，哈希不变）。

更新数据时重新向manifest所列权威来源取得数据、保留相同标准化字段、记录实际版本/处理/许可并更新哈希；不可只修改日期。完整重建命令见skill说明。格网尺度默认1km，统计比例先保留6位小数再分类，以便测量与理由可对照。

## 许可与署名

- WorldCover 2021 v200：[CC BY 4.0及数据使用说明](https://esa-worldcover.org/en/data-access)。© ESA WorldCover project 2021 / Contains modified Copernicus Sentinel data (2021) processed by ESA WorldCover consortium。
- 伦敦功能数据，上海界线与功能数据：[OpenStreetMap contributors，ODbL 1.0](https://www.openstreetmap.org/copyright)，标准化衍生文件在相同数据库许可下提供。
- 伦敦界线：Contains National Statistics data © Crown copyright and database right 2015; Contains Ordnance Survey data © Crown copyright and database right 2015。来源链接见manifest。
- 纽约：[NYC Open Data](https://data.cityofnewyork.us/) 与NYC Department of City Planning公开地理资料；[DCP分区元数据](https://s-media.nyc.gov/agencies/dcp/assets/files/pdf/data-tools/bytes/nyzd_metadata.pdf)说明规划用途与限制。资料无现状准确性保证。
- Broadway人工研究范围参考[Times Square Alliance](https://www.timessquarenyc.org/times-square-alliance/about-the-alliance)，并非复制官方精确风水边界。

HTML页尾保留数据署名，地图另保留OSM底图署名；项目代码许可不替代第三方数据许可。
