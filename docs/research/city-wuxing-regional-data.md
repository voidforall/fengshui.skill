# 城市五行地图：伦敦区域分析与地理数据调研

> 历史调研记录：下文的少量代表片区/待分析建议已被全城需求取代。当前实现采用完整城市边界和连续统计单元，每单元分类并标注置信等级；最新规则见 `skills/city-wuxing-map/references/method.md`。

调研日期：2026-11-15。范围：地理分区与数据依据；本报告不证明五行或风水效应，也不修改当前地图实现。

## 结论

用片区多边形表达“这一带以某种景观或功能为主”，比给孤立地标贴五行标签更符合用户提出的城市整体阅读需求。但应先确定区域的真实空间特征，再公开说明五行解释；不能因为区里有一座银行或剧院，就把整个行政区判成金或火。这里的五行映射是本项目分析选择，不是下列官方地理机构的分类。

行政边界与景观边界不是同一回事。Defra 说明国家景观特征区（NCA）综合景观、生物与地质多样性、历史、文化及经济活动划分，其边界沿自然景观线，而非郡或区界。因此 borough/ward 可以作为统计和展示容器，但不能被直接称作“天然风水边界”。[Defra 官方说明](https://www.gov.uk/guidance/national-character-area-profiles-information-for-local-decision-making)

## 已核对的一手框架

Natural England 的 **London’s Natural Signatures** 发布于 2011 年，划分 7 类景观类型、22 个自然景观区域。方法叠加基岩、表层地质、地形、土壤与生境；区域跨越 borough 边界。它是桌面研究框架，作者明确需要后续研究与咨询，不是现场逐宅评估。原文可从 Natural England 官方档案按章节下载。[完整目录](https://publications.naturalengland.org.uk/publication/6540238365130752)、[Introduction 正文，印刷页 7–8](https://publications.naturalengland.org.uk/file/5383771377369088)、[Landscape Types 章节，印刷页 23 起](https://publications.naturalengland.org.uk/file/4972599394172928)

GLA **2026 年 London Local Nature Recovery Strategy Annex 2** 的 §2.4 以 11 个景观区域汇总上述 22 个 Natural Signatures，图 2.1、2.2 展示两套分区。可用作区域分析的官方参照，但两套地图并不表示五行结论。[GLA Annex 2，印刷页 7–18](https://www.london.gov.uk/sites/default/files/2026-03/MoL_LNR_Strategy_ANNEX_2_FA.pdf)

## 数据可获得性：不能把 PDF 地图说成现成 GIS 边界

| 数据 | 本次实际核对到什么 | 对区域着色的用途与限制 |
|------|--------------------|------------------------|
| 22 个 Natural Signatures | 官方可下载资料是分章节 PDF，含范围图、描述和地理图层；本次**未找到并验证**官方 SHP/GeoJSON 多边形下载 | 适合作为分析范围与地貌证据。实施时仍须取得原始 GIS 几何，或将人工数字化边界标成“据官方图概化”，不能假装已有精确官方矢量区界 |
| LNRS 11 个 landscape areas | 核对到 2026 Annex 2 的 PDF 地图与文字；本次**未验证**这 11 个区域的可下载 GIS 多边形 | 是较粗的展示分区候选；不要与英格兰全国 48 个 LNRS 管辖范围混为一谈 |
| Borough / ward | GLA 发布实际 ESRI / MapInfo 边界 ZIP；本次下载并列出 `London-wards-2018.zip`，确认包含 `London_Ward.shp`、DBF、PRJ 等 | 可直接转换成 GeoJSON 作分区统计和着色；这个包是 **2018 边界**，目录更新日期不等于边界年份。当前边界应另核对相应年份 |
| London Green and Blue Cover | GLA 提供可下载绿/蓝覆盖 shapefile 及 borough、ward 汇总表，图层使用 EPSG:27700，数据基础为 2018 年 | 支持真实面积比例和空间分布证据，需转换坐标；不能把旧覆盖资料说成当前实测，不能由“可访问公园”替代所有绿地 |
| OS Open Greenspace | 官方提供 SHP / GeoPackage 等矢量数据，覆盖可公开进入的绿地及入口 | 支持公园等真实面状几何；并非所有树冠、私人花园或所有自然植被的全集 |
| OS Open Rivers | 官方提供水系矢量数据，核心是水系网络/概化中心线 | 支持河流连通关系；不能直接把中心线当作河面或“水相片区”多边形，不应随意加固定半径冒充真实区域 |
| OS Terrain 50 | 官方提供 50m 点距 DTM 与等高线，面向大范围地形分析 | 支持高地、坡势、河谷等区域证据；DTM 是去掉建筑和树木后的地表，不表示城市建筑轮廓 |

边界资料来源：[GLA 发布的边界目录](https://www.data.gov.uk/dataset/8ebe1b69-5348-4bc5-bf3b-694bc46ecc98/statistical-gis-boundary-files-for-london1)、[本次下载验证的 2018 ward ZIP](https://data.london.gov.uk/download/20od9/08d31995-dd27-423c-a987-57fe8e952990/London-wards-2018.zip)。地图须保留该目录要求的 National Statistics 与 OS 署名。

覆盖与地形来源：[GLA Green and Blue Cover](https://data.london.gov.uk/dataset/london-green-and-blue-cover-emqzm)、[OS Open Greenspace](https://www.ordnancesurvey.co.uk/products/os-open-greenspace)、[OS Open Rivers](https://www.ordnancesurvey.co.uk/products/os-open-rivers)、[OS Terrain 50](https://www.ordnancesurvey.co.uk/products/os-terrain-50)、[Terrain 50 官方技术说明](https://docs.os.uk/os-downloads/products/land-and-terrain-portfolio/os-terrain-50)。不同数据层需逐项核对许可、年份、坐标系和精度，不能因可在线浏览就推断可重新分发。

## 三个片区候选：分析假设，不是已定五行

| 片区候选 | 官方资料支持的事实 | 可以进一步分析的解释，尚未下结论 |
|----------|------------------|----------------------------------|
| Upper Thames 河谷带 | 曲折河道、潮间带、岛屿和洪泛草地，沿岸又有公园、林地及密集聚落 | 可考察“水为主、木为辅”的区域表达；但应按河谷实际范围和内部用地分布分段，不能将整个 Richmond borough 一色涂水。[Natural England：Upper Thames，印刷页 82–85](https://publications.naturalengland.org.uk/file/4657542873481216) |
| Hampstead Ridge | 高起山脊上的林地、灌丛、酸性草地，兼有城建、铁路与水体；不是仅 Primrose Hill 一个点 | 应分别检查山脊轮廓与林地分布；林地取木属于公开的现代山水取象口径，传统形法的主象还需看整体形态，不能因地势高就自动判成土形。[Natural England：Hampstead Ridge，印刷页 50–53](https://publications.naturalengland.org.uk/file/5234098477989888) |
| Lea River Valley | 河流、宽洪泛区、水库与人类显著改造的地貌相互叠加，南北沿线景观并不相同 | 可将河谷骨架作为水相分析起点，结合绿地、工业/居住等实际区域另划分；不能把整个长河谷直接等同一个同质区。[Natural England：Lea River Valley，印刷页 54 起](https://publications.naturalengland.org.uk/file/5423490161180672) |

## 地图设计推论（本项目建议）

区域面应为主层，地点为解释证据。每区保留：边界来源/年份/概化状态、主相与兼相、支撑事实、分析理由、反例或混合特征、资料来源。色彩表示本图选择的主相，纹理或标签表示兼相/不确定性。未分析区域保持中性，不能强行五等分，也不虚构“金 72 分、木 18 分”之类看似测量的数值。

最直接的下一步是先选少数有可靠边界和资料的连续景观片区，完成可解释的区域版伦敦示例。若首版必须以 ward 统计，标题应写清“按行政统计单元汇总”，保留内部异质性说明；这是可复现的表达方式，不是宣称行政线即自然相界。
