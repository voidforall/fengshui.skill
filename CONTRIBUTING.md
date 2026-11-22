# 参与贡献

欢迎勘误、补充出处和改进功能。先读 [工作原理](docs/how-it-works.md)，了解各个 skill 的分工和计算口径。

## 报告错误

请提 issue，并附上**出处**：典籍、卷次、原文，或其他可核对的资料。确认后会修正，并补一条覆盖它的测试。
规则与引文的出处登记在 [references/sources.md](references/sources.md)（八字见 [skills/bazi-mingli/references/sources.md](skills/bazi-mingli/references/sources.md)）；
新增规则先在这里登记出处与核对状态，再写代码。

## 开发约定

- **计算与呈现分开**：计算放在 `scripts/kanyu/` 的领域模块，参数处理在 `cli.py`，文字输出在 `render.py`，HTML 在 `pages.py` 与各 skill 的 `assets/templates/`。
- **计算包只有一份源头** `scripts/kanyu/`。八字 skill 带的副本和它的术语表 `references/glossary.md` 由同步脚本生成，不要直接改：

  ```bash
  python3 tools/sync_kanyu.py
  ```

- **`SKILL.md` 保持精简**，详细流程放进各 skill 的 `references/`。
- 调试时可以直接运行 skill 调用的入口：`python3 scripts/fengshui.py -h`、`python3 skills/bazi-mingli/scripts/bazi.py -h`。

## 测试

```bash
pip install -r requirements.txt -r skills/city-wuxing-map/requirements.txt
python3 -m unittest discover -s tests
node --test tests/city_search.test.cjs      # 城市地图地址搜索（Node 22）
```

- 未安装 `lunar_python` 时，历法相关用例会自动跳过；改历法相关代码时务必装上依赖再跑。
  CI 在 Python 3.10 和 3.13 上运行，装与不装 lunar_python 各跑一遍，并校验三个 skill 符合 Agent Skills 规范。
- **命令行快照**：有意修改输出后重新生成快照，并逐项检查 diff，不能用更新快照掩盖计算错误：

  ```bash
  UPDATE_GOLDEN=1 python3 -m unittest tests/test_cli.py
  git diff tests/golden/
  ```

- **交互示例**：改了 HTML 模板，按 [docs/examples/README.md](docs/examples/README.md) 重新生成示例，并在浏览器里检查。
- **模型评测**：见 [evals/README.md](evals/README.md)。

## 发版

在一个 PR 里同步提升 `scripts/kanyu/__init__.py` 与 `SKILL.md` 的版本号（再运行同步脚本），
并把 [CHANGELOG](CHANGELOG.md) 的 `## [Unreleased]` 改为 `## [版本号] - 日期`。
合并到 main 后，`.github/workflows/release.yml` 自动打 tag，并以 CHANGELOG 对应条目为正文发布 GitHub Release。

版本号遵循语义化版本：已安装 skill 的能力减少、默认结果改变，都算不兼容变更。
