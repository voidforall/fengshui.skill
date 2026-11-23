# 交互盘面示例

`feixing-demo.html` 由下面的命令生成（批注见 `feixing-notes.json`，与 `skills/fengshui-master/examples/yangzhai.md` 的对话一致）：

```bash
python3 skills/fengshui-master/scripts/fengshui.py feixing --facing 180 --year 2018-09-01 --annual 2026 \
        --html docs/examples/feixing-demo.html --notes docs/examples/feixing-notes.json
```

英文版 `feixing-demo.en.html`（批注 `feixing-notes.en.json`，同一套房子）：

```bash
python3 skills/fengshui-master/scripts/fengshui.py feixing --facing 180 --year 2018-09-01 --annual 2026 --lang en \
        --html docs/examples/feixing-demo.en.html --notes docs/examples/feixing-notes.en.json
```

修改 `skills/fengshui-master/assets/templates/feixing.html` 或 `lib/kanyu/` 后（先运行 `python3 tools/sync_kanyu.py`）请重新运行这两条命令；`tests/test_pages.py` 会检查示例是否过期。
README 中的动图与截图用 Playwright 录制（见 PR 说明），不参与测试。

## 八字命盘

`bazi-demo.html` 由下面的命令生成（批注见 `bazi-notes.json`）：

```bash
python3 skills/bazi-mingli/scripts/bazi.py --birth "1990-06-01 08:30" --gender f --longitude 116.4 --year 2026 \
        --html docs/examples/bazi-demo.html --notes docs/examples/bazi-notes.json
```

英文版 `bazi-demo.en.html`（批注 `bazi-notes.en.json`，同一张命盘）：

```bash
python3 skills/bazi-mingli/scripts/bazi.py --birth "1990-06-01 08:30" --gender f --longitude 116.4 --year 2026 --lang en \
        --html docs/examples/bazi-demo.en.html --notes docs/examples/bazi-notes.en.json
```

修改 `skills/bazi-mingli/assets/templates/bazi.html` 或 `lib/kanyu/` 后（先运行 `python3 tools/sync_kanyu.py`）请重新运行这两条命令；`tests/test_pages.py` 会检查示例是否过期。
在浏览器检查：「一眼看懂」、点术语弹出白话解释、「白话」开关、四柱翻开动画、点干支与弧线、大运卡片与年份拖动、「藏干」「合冲刑害」开关、时辰不详（三柱）、手机宽度与深色模式；英文版另查术语首次出现的拼音与汉字、长英文名换行、无横向滚动。
README 中的 `docs/images/bazi-chart.png` 用 Playwright 截取此页（2 倍像素）。

## 城市五行地图

从仓库根目录重新生成两座城市的交互示例：

```bash
python3 -m pip install -r skills/city-wuxing-map/requirements.txt
python3 skills/city-wuxing-map/scripts/generate.py --example london --output docs/examples/london-wuxing.html
python3 skills/city-wuxing-map/scripts/generate.py --example new-york --output docs/examples/new-york-wuxing.html
python3 skills/city-wuxing-map/scripts/generate.py --example shanghai --output docs/examples/shanghai-wuxing.html
python3 skills/city-wuxing-map/scripts/generate.py --example london --lang en --output docs/examples/london-wuxing.en.html
python3 skills/city-wuxing-map/scripts/generate.py --example new-york --lang en --output docs/examples/new-york-wuxing.en.html
python3 -m http.server 8000 --bind 127.0.0.1
```

访问 `http://127.0.0.1:8000/docs/examples/london-wuxing.html`、`new-york-wuxing.html` 或 `shanghai-wuxing.html`。这些示例内嵌 Leaflet、模板与区域几何和分析数据，真实地图瓦片需要联网，通过 HTTP 加载。直接双击 HTML 时只显示区域分析并提示启动本地服务。

原始区域资料在 `skills/city-wuxing-map/examples/`，修改模板、生成器、库文件或资料后都要重新生成这五个 HTML（英文示例只提交伦敦、纽约，上海英文页可用同样的 `--lang en` 生成）。`tests/test_city_map.py` 检查示例是否过期。README 截图来自实际浏览器加载后的伦敦地图，保留底图署名。

默认连续着色：伦敦1,735单元、纽约五区1,323单元、上海主城区1,857单元。检查城市边缘、岛屿与水域，所有单元在两种口径下都有分类。检查伦敦 `SW1A 1AA` / `SW1A` / `SW1`、纽约 `10013`、上海「陆家嘴」与 `31.2397,121.5055`、当地地址候选，以及坐标搜索、五行筛选、选中单元详情与置信等级、证据和格网线开关。源数据与离线重建方式见skill说明和examples/sources/README.md。
