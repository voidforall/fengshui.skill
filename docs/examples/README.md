# 交互盘面示例

`feixing-demo.html` 由下面的命令生成（批注见 `feixing-notes.json`，与 `examples/yangzhai.md` 的对话一致）：

```bash
python3 scripts/fengshui.py feixing --facing 180 --year 2018-09-01 --annual 2026 \
        --html docs/examples/feixing-demo.html --notes docs/examples/feixing-notes.json
```

修改 `assets/templates/feixing.html` 后请重新运行此命令；`tests/test_pages.py` 会检查示例是否过期。
README 中的动图与截图用 Playwright 录制（见 PR 说明），不参与测试。

## 城市五行地图

从仓库根目录重新生成两座城市的交互示例：

```bash
python3 skills/city-wuxing-map/scripts/generate.py --example london --output docs/examples/london-wuxing.html
python3 skills/city-wuxing-map/scripts/generate.py --example new-york --output docs/examples/new-york-wuxing.html
python3 -m http.server 8000 --bind 127.0.0.1
```

访问 `http://127.0.0.1:8000/docs/examples/london-wuxing.html` 或 `http://127.0.0.1:8000/docs/examples/new-york-wuxing.html`。这些示例内嵌 Leaflet、模板与区域几何和分析数据，真实地图瓦片需要联网，通过 HTTP 加载。直接双击 HTML 时只显示区域分析并提示启动本地服务。

原始区域资料在 `skills/city-wuxing-map/examples/`，修改模板、生成器、库文件或资料后都要重新生成两个 HTML。`tests/test_city_map.py` 检查示例是否过期。README 截图来自实际浏览器加载后的伦敦地图，保留底图署名。

区域版默认显示半透明多边形与主象/兼象，点位为可开关证据层。检查口径切换（如 Canary Wharf 的金/水主象变化）、灰色待分析、区域点击与边界来源；不能只确认若干点位能显示。
