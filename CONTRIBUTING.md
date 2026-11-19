# 参与开发

本文件写给改代码、改规则的人。使用方法见 [README](README.md)，运行时规则见各 skill 的 `SKILL.md`。

## 原则

- **计算交给代码，解读交给模型**：排盘、历法、查表都在 `scripts/kanyu/` 里确定性完成，并有测试覆盖；模型只负责问询、调用脚本和解读。
- **说法要有出处**：每条规则、引文的出处与核对状态登记在 [references/sources.md](references/sources.md)（八字见 [skills/bazi-mingli/references/sources.md](skills/bazi-mingli/references/sources.md)），
  分为原文已核对、已计算验证、公认出处、流派口径、已删除。新增规则先登记出处。
- **勘误**：欢迎提 issue，请注明出处（典籍卷次或可核对的资料）。确认后会补对应的测试。

## 命令行

skill 运行时会自动调用脚本，也可以直接运行。每个命令都可加 `--json` 输出结构化数据。

```bash
# 风水（fengshui-master）
python3 scripts/fengshui.py feixing --facing 180 --year 2018-09 --annual 2026 \
        --html 飞星盘.html --notes 批注.json                          # 玄空飞星 + 交互盘面
python3 scripts/fengshui.py bazhai --facing 90 --birth 1988-05-01 --gender m    # 八宅游年 + 命卦
python3 scripts/fengshui.py mingua --birth 1990-01-20 --gender f                # 命卦（按立春分年）
python3 scripts/fengshui.py liunian --year 2026 --span 5                        # 流年紫白、太岁、三煞
python3 scripts/fengshui.py day --date 2026-05-20                               # 单日四柱、建除、神煞、宜忌
python3 scripts/fengshui.py zeri --event 入宅 --start 2026-05-10 --end 2026-05-31 --birth-year 1988

# 八字（bazi-mingli）
python3 skills/bazi-mingli/scripts/bazi.py --birth "1990-06-01 08:30" --gender f --longitude 116.4 \
        --year 2026 --html 命盘.html --notes 批注.json                 # 八字 + 交互命盘
python3 skills/bazi-mingli/scripts/bazi.py --birth "1985-11-09 23:30" --lunar --gender m \
        --tz America/New_York --longitude -74.0                    # 农历输入、海外出生
python3 skills/bazi-mingli/scripts/bazi.py --birth 1985-12-20 --gender m    # 时辰不详：排三柱

# 城市五行地图（city-wuxing-map）
python3 -m pip install -r skills/city-wuxing-map/requirements.txt
python3 skills/city-wuxing-map/scripts/generate.py --example london --output docs/examples/london-wuxing.html
```

历法相关命令（`day`、`zeri`、八字）需要 `pip install -r requirements.txt`。

| 计算 | 实现 |
|------|------|
| 飞星排盘 | 二十四山玄空阴阳 + 同元龙定顺逆；替卦、兼向与空亡提示；格局判定（旺山旺向、上山下水、双星、伏反吟、合十、三般卦） |
| 八宅 | 依《八宅明镜》游年歌诀生成；命卦按立春分年，男五寄坤、女五寄艮 |
| 流年流月 | 紫白飞星、太岁、岁破、三煞、五黄二黑方 |
| 择日 | 干支、节气、建除、黄黑道、神煞、宜忌取自 lunar-python；月破、正四废、冲当事人做硬排除；岁破日、受死只标注 |
| 八字 | 年月柱按北京时间比对节气，日时柱用当地真太阳时，自动扣夏令时，子时默认 23:00 换日；藏干十神、长生、司令、旺相、合冲刑害、神煞依《三命通会》查表；调候检出《穷通宝鉴》原文。不判定旺衰、用神 |

## 代码结构

```
fengshui.skill/
├── SKILL.md                 # fengshui-master：铁律、人设、问题分流
├── references/              # 看宅、择日流程（playbook-*.md）、速查表、出处
├── assets/templates/        # 飞星盘模板
├── scripts/
│   ├── fengshui.py          # fengshui-master 命令行入口
│   └── kanyu/               # 计算包（唯一源头）：core、bazhai、feixing、zibai、almanac、zeri、
│                            #   ganzhi、bazi、glossary、render、pages、cli
├── skills/
│   ├── bazi-mingli/         # 八字 skill：SKILL、流程、术语表、出处、命盘模板、scripts/bazi.py、kanyu 副本
│   └── city-wuxing-map/     # 城市五行地图 skill
├── tools/sync_kanyu.py      # 把 scripts/kanyu/ 同步到子 skill，并生成 glossary.md
├── tests/                   # 单元测试与命令行快照（golden/）
├── evals/                   # 古籍案例端到端评测
├── docs/                    # README 用图与交互示例
└── examples/                # 完整对话示例
```

- 计算放在领域模块，参数处理在 `cli.py`，文字输出在 `render.py`，HTML 在 `pages.py` 与各 skill 的 `assets/templates/`。
- **只改 `scripts/kanyu/`**，改完运行 `python3 tools/sync_kanyu.py`。`tests/test_skill_bazi.py` 检查副本与生成的术语表是否一致。

## 测试

```bash
python3 -m unittest discover -s tests
node --test tests/city_search.test.cjs     # 城市地图地址搜索（Node 22）
```

- 未安装 `lunar_python` 时，历法相关用例会自动跳过。CI 在 Python 3.10 和 3.13 上运行，装与不装 lunar_python 各跑一遍，并用 `agentskills validate` 校验三个 skill。
- 测试用例取自可公开核对的结论（游年歌诀、各运旺山旺向表、紫白年星与 lunar-python 交叉验证、《三命通会》原文等）。派别有分歧的地方不进测试，在输出中提示。
- **命令行快照**：有意修改输出后重新生成，并逐项检查 diff，不能用更新快照掩盖计算错误：

  ```bash
  UPDATE_GOLDEN=1 python3 -m unittest tests/test_cli.py
  git diff tests/golden/
  ```

- **交互示例**：改了 HTML 模板后，按 [docs/examples/README.md](docs/examples/README.md) 重新生成示例，并在浏览器检查。
- **模型评测**：见 [evals/README.md](evals/README.md)。

## 发版

在一个 PR 里同步提升 `scripts/kanyu/__init__.py` 与 `SKILL.md` 的版本号（再运行 `python3 tools/sync_kanyu.py`），
并把 [CHANGELOG](CHANGELOG.md) 的 `## [Unreleased]` 改为 `## [版本号] - 日期`。
合并到 main 后，`.github/workflows/release.yml` 自动打 tag，并以 CHANGELOG 对应条目为正文发布 GitHub Release（tag 已存在则跳过）。
版本号遵循语义化版本：已安装 skill 的能力减少、默认结果改变，都算不兼容变更。
