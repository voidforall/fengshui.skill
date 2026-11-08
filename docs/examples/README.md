# 交互盘面示例

`feixing-demo.html` 由下面的命令生成（批注见 `feixing-notes.json`，与 `examples/yangzhai.md` 的对话一致）：

```bash
python3 scripts/fengshui.py feixing --facing 180 --year 2018-09-01 --annual 2026 \
        --rooms "大门=南,主卧=西北,厨房=东,卫生间=东北,客厅=中,书房=西" \
        --member "我:1985-03-01:m" --member "太太:1990-06-01:f" \
        --html docs/examples/feixing-demo.html --notes docs/examples/feixing-notes.json
```

修改 `assets/templates/feixing.html` 后请重新运行此命令；`tests/test_pages.py` 会检查示例是否过期。
README 中的动图与截图用 Playwright 录制（见 PR 说明），不参与测试。
