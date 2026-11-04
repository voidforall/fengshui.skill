# Changelog

版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。`SKILL.md` 的 `metadata.version`、
`scripts/kanyu/__init__.py` 的 `__version__` 与本文件最新条目保持一致（有测试校验）。

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

[2.1.0]: https://github.com/voidforall/fengshui.skill/compare/v2.0.0...v2.1.0
[2.0.0]: https://github.com/voidforall/fengshui.skill/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/voidforall/fengshui.skill/releases/tag/v1.0.0
