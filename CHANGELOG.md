# Changelog

版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。`skills/fengshui-master/SKILL.md` 的 `metadata.version`、
`lib/kanyu/__init__.py` 的 `__version__` 与本文件最新条目保持一致（有测试校验）。
新改动先记在 `## [Unreleased]` 下；发版时改为 `## [版本号] - 日期`，合并到 main 后自动发布 Release。

## [Unreleased]

### 英文支持（第一步）
- 三个 skill 改为中英双语触发：`description` 加英文说明与触发词（feng shui、flying stars、bazi、four pillars 等）。
- 新增各 skill 的 `references/english.md`（英文作答约定：英文意译在前、首次出现附拼音与简体汉字；引典籍先原文后译文并注明译者或「our translation」；白话优先）。
- 新增 `lib/kanyu/terms_en.py` 双语术语表，生成风水、八字的 `references/terms-en.md`；测试检查脚本输出的每个术语都有英文名。
- 有标准译名的术语按标准取：WHO《中医药国际标准术语》(2022) 与中华思想文化术语传播工程（如五行 Five Elements、相生 mutual generation、相克 mutual restraint、天干 Heavenly Stems、二十四节气 Twenty-four Solar Terms），出处逐条列在 `terms-en.md` 末尾；单个节气名、风水命理专名尚无标准，用通行译法。

### 英文支持（第二步）：英文交互盘面
- 飞星盘与八字命盘加 `--lang en` 生成英文页面：同一份模板中英双语，术语取自 `terms_en.py`，八字白话释义有英文版（`glossary.py`）。经典原文（《说卦》、《三命通会》天干物象与十二长生）照录中文，并附我们的译文；《穷通宝鉴》调候段保留原文，由模型在对话中翻译。
- 英文飞星盘用拼音与罗盘代号标山向（如 Zi (N2)）；英文命盘在干支字形下标拼音与五行，关系、神煞、大运流年、起运与排盘口径都是英文。
- 新增英文示例 `docs/examples/feixing-demo.en.html`、`bazi-demo.en.html`。

### 修复
- 飞星盘：洛书飞布轨迹线盖在九宫上，点击宫位中部时点不中。
- 八字命盘：旺相休囚死的「死」与十二长生的「死」同字，点「出生的季节」里的「死」会弹出十二长生的解释。

### 英文支持（第三步）：城市五行地图英文页面
- `generate.py --lang en` 生成英文地图：界面文字中英双语；每个单元的理由、事实、局限与置信说明由 `city_model.py` 按同一规则写出英文版，生成时核对主象、兼象、置信与中文数据一致。典籍引文照录原文并附我们的译文。
- 城市、范围、街道名取自数据的 `en` 对象（源快照 manifest 带入）；上海 113 个街道、镇名按汉语拼音转写、通名意译。
- 英文页面的地址搜索向 Photon 请求英文地名。新增英文示例 `docs/examples/london-wuxing.en.html`、`new-york-wuxing.en.html`。

### 新增
- 城市五行地图新增「相对取象」并设为默认（模型 `landcover-function-v2`）：依《尚书·洪范》五行之性与《五行大义》卷一「辨体性」（土「总于四行」），以土为底色，看各单元在范围内相对最突出的一行。上海由土 71% 变为金 16%、木 31%、水 17%、火 7%、土 29%；伦敦、纽约同规则重算。原综合口径改称「综合取象（绝对）」，仍可切换。
- 城市五行地图新增上海主城区示例：中心城区七区与浦东新区陆域，1,857 个 1km 单元（OSM 区界所含海域与外省飞地不纳入）。
- city-wuxing-map 支持可选 `scope_label`：范围不是整个市域时，页面标题与口径用「主城区」等代替「全城」；Postcodes.io 署名只在英国地图显示。
- 新增 `tools/prepare_city_sources.py`：从 OSM（Overpass）与 WorldCover 生成新城市的冻结源文件与 manifest，可复现。
- 以 MIT 许可证发布（`LICENSE`），三个 skill 的 `SKILL.md` 标注 `license: MIT`。第三方数据与 Leaflet 保留各自许可。

## [3.1.0] - 2026-11-23

三个 skill 统一放进 `skills/`，安装方式变为 `npx skills add voidforall/fengshui.skill --skill <名称>`，不再需要 `--full-depth`。
已安装的 skill 名称与功能不变。`bazi-mingli` 随之更新为 1.0.1（仅结构调整，功能不变）。

### 结构
- **三个 skill 统一放在 `skills/` 下**：`fengshui-master` 从仓库根目录移到 `skills/fengshui-master/`，与 `bazi-mingli`、`city-wuxing-map` 并列。
  安装不再需要 `--full-depth`：`npx skills add voidforall/fengshui.skill --skill <名称>`；不带 `--skill` 时在终端里列出三个 skill 勾选，
  在智能体里运行则全部安装（已用 skills CLI 实测）。已安装的 `fengshui-master` 名称不变。
- 计算包源头从 `scripts/kanyu/` 移到 `lib/kanyu/`，由 `tools/sync_kanyu.py` 复制到 `fengshui-master` 与 `bazi-mingli`。每个 skill 只带用到的模块
  （命令、文字输出、页面按风水、八字拆分），测试检查副本与源头一致且能单独导入；副本在 `.gitattributes` 标为生成文件，PR 中默认折叠。
- 测试、eval 工作区、CI 规范校验与发版工作流同步改为新路径。

### 文档
- README 精简为面向用户的首页（能做什么、安装、效果、为什么可信、参考典籍、路线图），不再列脚本命令；
  工作原理与计算口径移到 `docs/how-it-works.md`，勘误、开发约定、测试与发版移到新的 `CONTRIBUTING.md`。
- README 末尾加 Star History 图。

## [3.0.0] - 2026-11-18

主版本号提升，因为有两处不兼容变更：
- `fengshui.py bazi` 不再排盘，改为提示迁移到 bazi-mingli（`skills/bazi-mingli/scripts/bazi.py`，参数相同）；
- 八字子时默认改为 23:00 起换日，23 点后出生者的日柱可能与旧版不同（加 `--zi same` 可按旧口径排）。

新增独立 skill `bazi-mingli` 1.0.0。

### 结构
- **八字拆为独立 skill `bazi-mingli`**（`skills/bazi-mingli/`，入口 `scripts/bazi.py`），可单独安装：
  `npx skills add voidforall/fengshui.skill --full-depth --skill bazi-mingli`。`fengshui-master` 不再排八字，
  `fengshui.py bazi` 改为提示迁移；按喜用五行配合风水仍在主 skill。
- 计算包仍只有一份源头 `scripts/kanyu/`，由 `tools/sync_kanyu.py` 同步到子 skill，测试检查两边一致。
- eval 工作区同时安装两个 skill。

### 八字
- **白话化**：命盘顶部新增「一眼看懂」（模型的白话总结 + 日主物象、出生季节旺相休囚死、五行个数、当前大运流年）；
  术语可点开看白话解释，「白话」开关标出十神、长生的一词释义，页尾术语表。释义集中在 `kanyu/glossary.py`，
  同步生成 `references/glossary.md`；物象、长生比喻、旺相休囚死均取《三命通会》原文，十神白话标为通行释义。
- 流程新增「先白话、后专业」的作答结构，批注新增 `plain`（白话总结）。
- 新增旺相休囚死（《三命通会》卷二），文字输出与命盘都给出日主在出生季节的状态。
- 出生时间口径：按 IANA 时区自动扣夏令时（中国大陆 1986–1991 年夏季此前未处理，时柱可能差一个时辰）；`--tz` 支持海外出生；
  年柱、月柱按同一时刻的北京时间比对立春与节气，日柱、时柱用出生地真太阳时。
- 子时换日：新增 `--zi next|same`。**默认改为 23:00 起换日**（原为 lunar-python 默认的晚子时日柱不换）；23 点后出生时两种都列出。
- 时辰不详：`--birth` 只给日期时排三柱，并提示起运误差与当日交节。新增农历输入 `--lunar`（闰月加 `--leap`）。
- 事实层（新模块 `ganzhi.py`，纯标准库）：藏干十神、十二长生、月令人元司事、通根、透干、原局干支五合、六合、冲、刑、害、三合（缺一不成局）、三会，
  禄、羊刃、天乙贵人、驿马、咸池、空亡查表，均据《三命通会》卷二、卷三原文核对。
- 《穷通宝鉴》调候原文索引：日干 × 节气月共 120 格，只录原文（专论、合论、季论），由 `evals/tools/build_qiongtong.py` 从维基文库原文生成。
- 起运交运日期与周岁；十步大运，每步展开十个流年，标出与原局的合冲刑害；`--year` 指定重点看的流年。
- 交互命盘 `bazi --html --notes`：四柱依次翻开、柱间弧线标关系、点干支看通根透干，大运流年可点选与拖动，支持手机与深色模式。
- 八字流程（`skills/bazi-mingli/references/playbook.md`）重写：问询出生时间、论命顺序（调候、月令、通根透干、燥湿、合冲、从化、定用神并写依据）、按问题分流与表达边界。

## [2.3.0] - 2026-11-15

### 新增
- 城市地图支持本地适用的邮编、邮区、地址及地区名定位；英国专用邮编查询与通用多语言候选搜索，保留服务失败、范围外和中心点语义。
- 独立 `city-wuxing-map` skill：完整城市连续着色，主象、兼象、置信等级、事实与解释分开呈现。
- 大伦敦1,735单元、纽约五区1,323单元；冻结完整边界、WorldCover2021及功能数据与来源哈希，可离线重建。纽约规划数据明确区分许可用途和现状。
- schema 3与Shapely拓扑校验拒绝漏区、越界、重叠及缺失分类；综合与土地覆盖两种视图均逐单元分析。
- 支持坐标定位、行政区搜索、五行筛选及本单元证据点，格网线可开关；README、来源许可、生成命令与CI同步更新。

### 发布验证
- 发布工作流安装地图几何依赖，并执行地址搜索测试，确保完整城市覆盖校验不会因缺少依赖而跳过。

## [2.2.0] - 2026-11-07

### 结构
- 按 Agent Skills 规范做内部拆分：SKILL.md 精简为铁律、人设与问题分流（341 → 约 130 行），
  各用例流程移入 `references/playbook-yangzhai.md`、`playbook-zeri.md`、`playbook-bazi.md`，按需读取。
- 交互盘面模板移至 `assets/templates/`。
- 规则资料之间不再互相链接（规范：引用只有一层）；`tests/test_structure.py` 检查。
- CI 新增 Agent Skills 规范校验（`agentskills validate`）。
- 修正八字流程中残留的「材质建议」（已于出处核对时删除）。

### 交互盘面
- `feixing --html [路径] --notes 批注.json`：生成可交互的飞星盘（单个 HTML，离线可开，适配手机与深色模式）。
  二十四山罗盘、坐向线、九宫分层（运盘 / 山星 / 向星 / 流年 / 流月）、「起盘」按洛书逐宫飞布、点宫看《说卦》取象与批注。
- SKILL：排了飞星盘默认生成盘面，并在回答中给出链接；模型的解读以批注 JSON 传入，星数一律由脚本给出。
- README 首屏加入起盘动图，新增可视化路线图（罗盘定向、户型对位、八宅方位、择日月历、八字命盘、起卦）。

### 经典案例 eval
- 新增 `dayun_from_pillars()`（四柱 + 性别排大运）；一次性核对《滴天髓阐微》485 个命例书中所列大运全部一致，测试只保留代表例。
- 端到端 eval（`evals/`）：22 道古籍案例题（《滴天髓阐微》《穷通宝鉴》《神峰通考》《古今图书集成·堪舆部纪事》），
  `evals/run.py` 以 Claude Code 无头模式作答，评分模型对照原文判「一致 / 部分一致 / 不一致」，另有关键字与 skill 触发检查。
- 原文抓取、命例抽取、建题脚本见 `evals/tools/`。

### 出处核对
- 新增 `references/sources.md`：每条规则 / 引文的出处与核对状态（原文已核对、已计算验证、公认出处、流派口径、已删除）。
  原文取自维基文库所收《宅经》《葬书》《地理辨正》《天玉经内传》《撼龙经》《说卦传》《三命通会》《渊海子平》《五行大义》。
- SKILL 新增「说法要有出处」铁律：按核对状态措辞，不把通行做法说成经典原文。
- 新增测试：命卦、年紫白与古法三元起例逐年对照；文中提到的典籍必须登记在 sources.md。

### 修正
- 「山上龙神不下水」出自《青囊序》（原误作《玄空秘旨》）；「地善即苗茂，宅吉即人荣」为《宅经》引《三元经》（原误作《黄帝宅经》云，且「即」误作「则」）。
- 择日月份以节气为界（原误按农历月）；受死约每 12 天一次（原误作一年 12 次）。
- 地支方位区分八字「四方」与风水「二十四山所在宫」（原表混用）。

### 变更
- 最低支持 Python 3.10（3.9 已停止维护，GitHub 新版 Ubuntu 运行器不再提供）；CI 升级 checkout@v5、setup-python@v6。
- 岁破日、受死改为「通书俗忌」：择日只标注（△）不排除，因其不在《协纪辨方书》体系日神之列。
- 删除查无出处的内容：五行配材质、化煞物品、建除逐项宜忌表、红沙日、「科技」等现代取象、「某吉神可解诸凶」等说法。

## [2.1.0] - 2026-11-04

### 变更
- 计算脚本拆分为 `scripts/kanyu/` 包（core / bazhai / feixing / zibai / almanac / zeri / bazi / render / cli）。
  `scripts/fengshui.py` 仍是入口，命令与输出不变。
- 计算函数返回结构化数据，文字格式化统一在 `render`。

### 新增
- 所有命令支持 `--json` 结构化输出；`--version` 显示版本。
- 测试按模块拆分（23 → 65 个用例），新增命令行输出快照测试（`tests/golden/`）。
- GitHub Actions CI：Python 3.9 / 3.13 × 有 / 无 `lunar_python`。

## [2.0.0] - 2026-11-04

v1 的核心规则存在大量错误，本版本修正并改为「计算交给脚本，解读交给模型」。

### 修正
- **八宅游年表**：64 格中 30 格错误，改为依《八宅明镜》游年歌诀生成。
- **命卦**：女命得 5 应寄艮（原误为坤）；补充 2000 年后出生的公式；年份以立春为界。
- **玄空飞星顺逆**：原误用八字地支阴阳代替玄空二十四山阴阳；改为按同元龙之山定顺逆。
- **九运格局表**：原称「午山子向旺山旺向」「子山午向上山下水」，实为双星到向 / 双星到坐（九运下卦无旺山旺向）。
- **流年紫白表**：整体错一年（2026 年中宫为一白，原写二黑）。
- **示例**：八运子山午向的飞星盘为编造（实为双星到向）；「门朝东 = 震宅」应为兑宅；择日示例的日期原为估算。

### 新增
- `scripts/fengshui.py`：玄空飞星（下卦 / 替卦、兼向与空亡提示、格局判定）、八宅、命卦、流年流月紫白、
  单日历法、择日筛选、八字排盘。
- 回归测试：游年歌诀、七 / 八 / 九运旺山旺向与上山下水表、紫白年月星与 lunar-python 交叉验证。
- `SKILL.md`「铁律」：凡涉及计算必须调用脚本，禁止心算。

### 移除
- 虚构的「江南三元世家第七代传人」师承人设。

## [1.0.0]

- 初版：`SKILL.md` 人设与知识框架、参考资料、示例对话。
  **注意：此版本的八宅游年表、命卦、飞星规则、流年表存在错误，请勿使用。**

[2.3.0]: https://github.com/voidforall/fengshui.skill/compare/v2.2.0...v2.3.0
[2.2.0]: https://github.com/voidforall/fengshui.skill/compare/v2.1.0...v2.2.0
[2.1.0]: https://github.com/voidforall/fengshui.skill/compare/v2.0.0...v2.1.0
[2.0.0]: https://github.com/voidforall/fengshui.skill/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/voidforall/fengshui.skill/releases/tag/v1.0.0
