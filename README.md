# 堪舆子 · 传统风水顾问

> 「峦头为体，理气为用。」（堪舆家常言）

**一个遵循 [Agent Skills 开放标准](https://agentskills.io) 的 Skill，将传统堪舆学蒸馏为可对话的风水顾问。** 运用玄空飞星、八宅明镜、择日学等传统方法，帮助你分析居住环境、选择吉日、化解煞气。

本 Skill 由一份符合标准的 `SKILL.md`、参考资料和一个确定性计算脚本组成，不绑定任何特定工具——可在 Claude Code、Codex CLI 等 30+ 支持 [Agent Skills](https://github.com/agentskills/agentskills) 标准的智能体中直接使用。

---

## 这是什么

传统风水（堪舆学）是一套研究居住环境与人居关系的学问，包含形势（地理格局）与理气（方位气场）两大体系。本 Skill 将其核心方法论编码为 AI 智能体可执行的知识框架，使其能够：

- 根据房屋朝向、入住时间，**排布玄空飞星盘**，判断旺位凶位
- 依据居住者命卦，**配合八宅游年**，给出四吉四凶方布局建议
- 结合年月神煞，**筛选入宅/开业/动土吉日**，给出可操作时间窗口
- 识别路冲、天斩、壁刀等**常见外煞**，提供化解方案
- **解读风水术语**与经典原文，回答堪舆学理论问题

**计算交给代码，解读交给模型。** 大模型擅长问询与解释，但并不擅长排盘、推算干支节气——这些地方「看起来对」的错误最难被发现。因此本 Skill 内置 `scripts/fengshui.py`，所有排盘、查表、历法计算由脚本确定性完成，并有回归测试覆盖；模型只负责收集信息、调用脚本、解读结果。

不是玄学算命，不卖风水摆件，不恐吓煞气。基于《沈氏玄空学》《地理五诀》《协纪辨方书》等传统典籍的系统性方法。

---

## 安装

本项目遵循 [Agent Skills 开放标准](https://agentskills.io)（`SKILL.md` + YAML frontmatter），可用官方跨工具安装器 [`npx skills`](https://github.com/vercel-labs/skills) 一键装进 Claude Code、Codex CLI 及其他兼容工具，也可手动 clone。

### 方式一：npx skills（推荐，Claude Code / Codex CLI 通用）

```bash
# 自动检测项目内已使用的智能体（Claude Code / Codex 等）并安装
npx skills add voidforall/fengshui.skill

# 指定安装到 Codex CLI（写入 .agents/skills/ 或 ~/.codex/skills/）
npx skills add voidforall/fengshui.skill --agent codex

# 指定安装到 Claude Code（写入 .claude/skills/ 或 ~/.claude/skills/）
npx skills add voidforall/fengshui.skill --agent claude-code

# 安装到用户全局目录而非当前项目
npx skills add voidforall/fengshui.skill -g
```

`npx skills` 由 [vercel-labs/skills](https://github.com/vercel-labs/skills) 维护，支持 70+ 智能体，`--agent` 也可写 `cursor`、`opencode`、`windsurf` 等其他兼容工具名。

### 方式二：手动安装

按你使用的工具，clone 到对应的 skills 目录即可（目录名不强制，仅需包含 `SKILL.md`）：

```bash
# Claude Code
git clone https://github.com/voidforall/fengshui.skill ~/.claude/skills/fengshui-master

# Codex CLI
git clone https://github.com/voidforall/fengshui.skill ~/.codex/skills/fengshui-master
```

### 依赖

- Python 3.9+（飞星、八宅、命卦、流年只用标准库）
- 择日、单日黄历、八字需要历法库 [lunar-python](https://github.com/6tail/lunar-python)：

```bash
pip install -r requirements.txt   # 即 pip install lunar_python
```

---

## 使用方法

安装后，在支持该 Skill 的智能体（Claude Code、Codex CLI 等）中用自然语言描述需求即可触发。**无需特定指令**，以下场景均能自动识别：

### 阳宅分析

```
我家坐北朝南，2018年入住，最近财运不好，帮我看看风水格局
```

```
新家东南朝向，想知道主卧应该放在哪个方位，我是1990年的男性
```

### 择日

```
打算今年6月搬新家，帮我选几个入宅吉日，我是1988年男，门朝东
```

```
公司9月份想开业，什么日子比较好？
```

### 煞气与化解

```
我家大门正对着一条笔直的道路，这算不算路冲？怎么化解？
```

### 风水问答

```
八宅游年是什么？怎么算命卦？
```

```
九运是从哪年开始的？对风水布局有什么影响？
```

```
《青囊序》里「山上龙神不下水」是什么意思？
```

---

## 知识体系

| 流派 | 核心方法 | 用途 |
|------|---------|------|
| **三元玄空飞星** | 九宫飞布、元运、山星向星 | 阳宅旺衰、财运人丁判断 |
| **八宅明镜** | 东西四宅命、游年变卦 | 卧室书房财位布局 |
| **形势峦头** | 龙穴砂水向、藏风聚气 | 外部环境与煞气判断 |
| **择日学** | 建除十二神、月破三煞 | 入宅开业动土选日 |
| **八字配风水** | 日主用神、五行方位 | 个人旺方与颜色建议 |

---

## 计算脚本

Skill 运行时会自动调用，也可以直接在命令行使用：

```bash
python3 scripts/fengshui.py feixing --facing 180 --year 2018-09 --annual 2026   # 玄空飞星排盘
python3 scripts/fengshui.py bazhai --facing 90 --birth 1988-05-01 --gender m    # 八宅游年 + 命卦
python3 scripts/fengshui.py mingua --birth 1990-01-20 --gender f                # 命卦（自动按立春分年）
python3 scripts/fengshui.py liunian --year 2026 --span 5                        # 流年紫白、太岁、三煞
python3 scripts/fengshui.py day --date 2026-05-20                               # 单日四柱、建除、神煞、宜忌
python3 scripts/fengshui.py zeri --event 入宅 --start 2026-05-10 --end 2026-05-31 --birth-year 1988
python3 scripts/fengshui.py bazi --birth "1990-06-01 08:30" --gender f --longitude 116.4
```

每个命令都可以加 `--json` 输出结构化数据，便于程序处理。

| 计算 | 实现 |
|------|------|
| 飞星排盘 | 二十四山玄空阴阳 + 同元龙定顺逆，支持替卦、兼向/空亡提示、格局判定（旺山旺向、上山下水、双星、伏反吟、合十、三般卦） |
| 八宅 | 依《八宅明镜》游年歌诀生成，命卦自动按立春分年、男五寄坤女五寄艮 |
| 流年流月 | 紫白飞星、太岁、岁破、三煞、五黄二黑方 |
| 历法择日 | 干支、节气、建除、黄黑道、神煞、宜忌取自 lunar-python；月破、岁破、受死、正四废、冲当事人做硬排除 |

### 测试

```bash
python3 -m unittest discover -s tests
```

未安装 `lunar_python` 时，历法相关用例会自动跳过。CI 在 Python 3.9 / 3.13、装与不装 lunar_python 四种组合下运行。

命令行输出有快照测试（`tests/golden/`）。有意修改输出格式后，重新生成快照并检查 diff：

```bash
UPDATE_GOLDEN=1 python3 -m unittest tests/test_cli.py
git diff tests/golden/
```

测试用例取自可公开核对的结论（游年歌诀、七/八/九运旺山旺向与上山下水表、紫白年星与 lunar-python 交叉验证等）。派别有分歧的地方不进测试，而是在输出中提示。

### 版本

变更记录见 [CHANGELOG.md](CHANGELOG.md)。v1.0.0 的八宅、命卦、飞星规则存在大量错误，已在 v2.0.0 修正，请使用 v2 及以上版本。

### 勘误

发现错误？欢迎提 issue，请注明**出处**（典籍卷次或可核对的资料）。确认后会补充对应的测试用例。

---

## 文件结构

```
fengshui.skill/
├── SKILL.md                    # 主 Skill（人物设定 + 知识框架 + 执行流程，计算一律调用脚本）
├── scripts/
│   ├── fengshui.py             # 命令行入口（SKILL 调用这里）
│   └── kanyu/                  # 确定性计算包
│       ├── core.py             #   二十四山、九宫、洛书飞泊、元运（纯标准库）
│       ├── bazhai.py           #   八宅：命卦、游年
│       ├── feixing.py          #   玄空飞星：排盘、格局、替卦、兼向
│       ├── zibai.py            #   流年流月紫白、年家煞方
│       ├── almanac.py          #   历法：立春分年、节气月、单日信息、真太阳时
│       ├── zeri.py             #   择日：硬排除规则 + 打分
│       ├── bazi.py             #   八字排盘
│       ├── render.py           #   文字输出（计算模块不做格式化）
│       └── cli.py              #   参数解析、--json
├── tests/
│   ├── test_<模块>.py          # 每个模块一份单元测试
│   ├── test_cli.py             # 命令行快照、JSON、出错路径
│   └── golden/                 # 命令行输出快照
├── CHANGELOG.md                # 变更记录
├── requirements.txt            # lunar_python（历法）
├── references/
│   ├── feixing.md              # 玄空飞星速查（九宫飞布规则、各运旺衰、流年星表）
│   ├── wuxing-ganzhi.md        # 五行干支速查（天干地支、生克、命卦算法）
│   └── zeri.md                 # 择日神煞速查（建除十二神、月破、三煞、受死日）
└── examples/
    ├── yangzhai.md             # 完整阳宅分析对话示例（含飞星盘排布过程）
    └── zeri-example.md         # 完整择日对话示例（含命卦配合）
```

---

## 人物设定

**堪舆子**：研习传统堪舆的顾问。主修玄空飞星，兼通八宅明镜与形势峦头，择日参《协纪辨方书》体系。不虚构师承身份。

风格：引经据典但解释清晰，先问情况再下结论，不夸大风水作用，对伪术直接指出。

> 「《宅经》引《三元经》云：地善即苗茂，宅吉即人荣。风水能提供有利条件，左右吉凶概率，非决定命运之术。」

---

## 参考典籍

- 《宅经》（黄帝宅经）
- 《葬书》（郭璞）
- 《天玉经》《青囊序》（杨筠松）
- 《地理五诀》（赵九峰）
- 《玄空秘旨》
- 《沈氏玄空学》（沈竹礽）
- 《协纪辨方书》（清·允禄等）

---

## 相关项目

本项目遵循 **Agent Skills 开放标准**，也属于 **Persona Distill Skill** 生态的一部分——将特定领域的知识体系与专家视角蒸馏为跨工具可复用的 Skill。

- [agentskills/agentskills](https://github.com/agentskills/agentskills) — Agent Skills 开放标准规范
- [vercel-labs/skills](https://github.com/vercel-labs/skills) — `npx skills` 跨工具安装器
- [anthropics/skills](https://github.com/anthropics/skills) — 官方 Skill 仓库
- [nuwa-skill](https://github.com/alchaincyf/nuwa-skill) — 从公众人物蒸馏思维框架
- [awesome-persona-distill-skills](https://github.com/xixu-me/awesome-persona-distill-skills) — Persona Skill 合集

---

## 免责声明

本项目基于传统堪舆学理论，仅供学习、参考与文化探讨。风水为辅，人为为主。重大居住与人生决策请结合实际情况综合考量，勿作为唯一依据。
