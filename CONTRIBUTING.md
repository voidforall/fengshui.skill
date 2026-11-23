# 参与贡献

欢迎勘误、补充出处和改进功能。先读 [工作原理](docs/how-it-works.md)，了解各个 skill 的分工和计算口径。

## 报告错误

请提 issue，并附上**出处**：典籍、卷次、原文，或其他可核对的资料。确认后会修正，并补一条覆盖它的测试。
规则与引文的出处登记在各 skill 的出处表：[风水](skills/fengshui-master/references/sources.md)、[八字](skills/bazi-mingli/references/sources.md)；
新增规则先在这里登记出处与核对状态，再写代码。

## 开发约定

- **每个 skill 一个目录** `skills/<name>/`，目录名即 skill 名，各自带 `SKILL.md`、`references/`、`assets/`、`scripts/`。
- **计算与呈现分开**：计算放在 `lib/kanyu/` 的领域模块；命令、文字输出、页面按领域分为 `cli_fengshui` / `cli_bazi`、`render` / `render_bazi`、`pages_feixing` / `pages_bazi`，公共部分在 `cli`、`pages`。风水与八字模块互不导入。
- **计算包只有一份源头** `lib/kanyu/`。每个 skill 安装后是独立目录，所以要自带一份真实文件（指向目录外的符号链接在安装时会被丢掉）。
  各 skill 的 `scripts/kanyu/` 副本只带清单里列出的模块（见 `tools/sync_kanyu.py` 的 `MANIFEST`），和八字的术语表 `references/glossary.md` 一样由同步脚本生成，不要直接改；新增模块要加进清单：

  ```bash
  python3 tools/sync_kanyu.py
  ```

- **中英双语**：规则只写一份中文；英文作答约定在各 skill 的 `references/english.md`。英文术语只在 `lib/kanyu/terms_en.py` 维护，同步脚本生成各 skill 的 `references/terms-en.md`；脚本新增术语时同时补英文（`tests/test_terms_en.py` 会检查）。
- **`SKILL.md` 保持精简**，详细流程放进各 skill 的 `references/`。
- 调试时可以直接运行 skill 调用的入口：`python3 skills/fengshui-master/scripts/fengshui.py -h`、`python3 skills/bazi-mingli/scripts/bazi.py -h`。

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
- **新增城市地图**：用 `python3 tools/prepare_city_sources.py <城市>`（联网，城市配置写在脚本里）从 OSM 与 WorldCover 生成冻结源文件和 manifest，再按 city-wuxing-map 的说明构建与生成，并把来源、范围取舍写进 `examples/sources/README.md`。
- **模型评测**：见 [evals/README.md](evals/README.md)。

## 发版

在一个 PR 里同步提升 `lib/kanyu/__init__.py` 与 `skills/fengshui-master/SKILL.md` 的版本号（再运行同步脚本），
并把 [CHANGELOG](CHANGELOG.md) 的 `## [Unreleased]` 改为 `## [版本号] - 日期`。
合并到 main 后，`.github/workflows/release.yml` 自动打 tag，并以 CHANGELOG 对应条目为正文发布 GitHub Release。

版本号遵循语义化版本：已安装 skill 的能力减少、默认结果改变，都算不兼容变更。
