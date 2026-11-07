# 经典案例 eval

检验 skill 的结论是否与古籍一致。**标准答案是古籍原文的结论**：只说明 skill 是否忠实于典籍，
不说明命理、风水本身是否灵验。

## 两层

| 层 | 内容 | 是否调用模型 | 位置 |
|---|---|---|---|
| 第 1 层 | 古籍中「输入 → 确定结果」的部分，直接写成单元测试 | 否 | `tests/` |
| 第 2 层 | 需要判断的部分：让 skill 作答，再由评分模型对照古籍原文判分 | 是 | `evals/` |

### 第 1 层（已在 CI 中运行）

- **大运排法**（`tests/test_dayun.py`）：自任铁樵《滴天髓阐微》原文抽取 487 个命例的四柱与书中所列大运，
  脚本 `dayun_from_pillars()` 逐一对照，485 例全部一致；2 例书中未注性别，单独标注。
  另有 20 例大运不连续（原书或录入笔误），未收录。数据见 `tests/data/ditiansui_dayun.json`。
- 命卦、紫白与三元起例对照（`tests/test_sanyuan.py`）等，见 `references/sources.md`。

### 第 2 层

案例在 `evals/cases.json`，每题都附古籍原文引文（`source.quote`）与出处：

| 类别 | 题数 | 来源 |
|---|---|---|
| 八字 | 19 | 《滴天髓阐微》10、《穷通宝鉴》6（命例 3、逐月调候 3）、《神峰通考》3 |
| 形势 | 1 | 《三国志·管辂传》（管辂相毌丘俭墓） |
| 年神 | 1 | 《酉阳杂俎》（太岁上掘坑） |
| 诚实边界 | 1 | 《后汉书·郭镇传》（吴雄不择葬地、不避忌讳而三世廷尉） |

后三类转引自《古今图书集成·艺术典·堪舆部纪事》（第 680 卷）。原文均取自维基文库所收古籍（公有领域）。

每题判分：

- **评分模型**：对照原文给出「一致 / 部分一致 / 不一致」及理由
- **关键字**（不调用模型）：回答中是否出现案例要求的字，如用神五行
- **是否触发 skill、是否调用了脚本**

## 运行

需要已登录的 Claude Code（`claude` 命令）。

```bash
python3 evals/run.py --dry-run                        # 校验案例、列出题目，不花钱
python3 evals/run.py --case dts-001 --case kanyu-taisui
python3 evals/run.py --category 八字 --jobs 3
python3 evals/run.py --model sonnet --judge-model sonnet   # 用较便宜的模型
```

结果写入 `evals/results/<时间戳>/`（每题一个 JSON 和 `summary.md`），不提交到 git；
基线摘要见 `evals/results/baseline.md`。

**花费**：每题两次调用（作答 + 判分）。用默认模型时每题约 0.3–1 美元，全部 22 题约 10–20 美元；
用 `--model sonnet` 可明显降低。

## 新增案例

1. 用 `evals/tools/fetch_wikisource.py` 下载原文（每次请求间隔 45 秒，遵守维基文库限流；**不要抓取 ctext.org**，其禁止自动下载）。
2. 在 `evals/tools/build_cases.py` 中加题：引文从原文程序化截取，不要手抄。
3. 新用到的典籍登记到 `references/sources.md`。
4. `python3 evals/run.py --dry-run` 校验。

## 尚缺

- **玄空飞星宅例**：带坐向、元运、飞星盘与断语的实例基本只见于《沈氏玄空学》《宅运新案》，
  维基文库与公开网络均未找到可靠全文。若有原文（只用原文，不用现代评注本），可补为第 1 层（排盘逐宫比对）与第 2 层（断语）。
- 《子平真诠》维基文库未收。
