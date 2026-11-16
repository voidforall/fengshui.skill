# 仓库协作约定

## 项目边界

这是一个遵循 Agent Skills 标准的传统堪舆顾问 skill。项目介绍、命令用法与发布流程以 `README.md` 为准；运行时问询、分流与表达规则以 `SKILL.md` 为准。

- 计算交给 `scripts/kanyu/` 的确定性代码，模型负责问询与解读。不要用模型推算替代排盘、历法、命卦等计算。
- 修改传统规则或引文前，核对 `references/sources.md` 的出处与验证状态；区分经典原文、已验证计算与流派口径，不虚构出处。
- 不夸大风水作用，不作恐吓式断言，不把传统规则的符合程度表述为现实效果的证明。

## 修改方式

- `scripts/fengshui.py` 是命令行入口；计算放在对应领域模块，参数处理放在 `scripts/kanyu/cli.py`，文字输出放在 `scripts/kanyu/render.py`，HTML 生成放在 `scripts/kanyu/pages.py` 与 `assets/templates/`。保持计算与呈现分离。
- 保持纯标准库计算路径可用；历法依赖见 `requirements.txt`，缺失依赖时保留明确提示，不以猜测结果兜底。
- 保持 `SKILL.md` 精简，详细流程放在 `references/playbook-*.md` 并从主文件分流；结构约束见 `tests/test_structure.py`。
- 优先采用简单、直接的端到端实现；技术取舍优先考虑质量、简单性、稳健性、扩展性和长期维护，不因节省开发成本牺牲这些目标。
- 修复 bug 时，先通过用户实际使用的 CLI 或交互页面复现，再修改并补充能覆盖真实问题的回归测试。检查页面时也修正明显的视觉问题。

- 城市地图以 `skills/city-wuxing-map/SKILL.md` 为准；示例须覆盖完整声明范围，每单元保留分类、来源与置信说明，不虚构地理证据。

## 验证

- 常规测试：`python3 -m unittest discover -s tests`。CI 矩阵与 skill 校验命令以 `.github/workflows/tests.yml` 为准；缺少 `lunar_python` 时历法测试会跳过，涉及历法改动时须安装依赖并确认相关测试实际运行。
- 有意调整 CLI 输出后，按 `README.md` 的快照更新命令重新生成 `tests/golden/`，逐项检查 diff，不能用更新快照掩盖计算错误。
- 城市地图拓扑校验依赖 `skills/city-wuxing-map/requirements.txt`；源数据重建另需该目录的 `requirements-build.txt`。地址搜索另运行 `node --test tests/city_search.test.cjs`（Node 22）。模板或输入变更后按 `docs/examples/README.md` 重新生成示例，保留第三方数据和底图署名。
- 修改飞星或八字 HTML 模板后，按 `docs/examples/README.md` 重新生成示例，并在浏览器检查动画、点选批注、移动端与深色模式。
- 修改 eval 案例后运行 `python3 evals/run.py --dry-run`；模型评测流程及结果提交边界见 `evals/README.md`。
- 仅文档改动检查内容准确性、引用路径及 `git diff --check`，不必为文案新增测试。

## 提交与维护

- 提交只包含当前任务相关改动；commit message 不自动添加 agent 为 co-author。
- 发版时按 `README.md` 同步版本与 `CHANGELOG.md`；普通改动不要随意提升版本号。
- 本文件只保留对多数后续会话都有用的约定。优先重写、删减并指向权威文件，避免复制容易过时的实现细节。
