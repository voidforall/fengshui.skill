# 堪舆子 · 传统风水与八字顾问

**中文** · [English](README.en.md)

[![tests](https://github.com/voidforall/fengshui.skill/actions/workflows/tests.yml/badge.svg)](https://github.com/voidforall/fengshui.skill/actions/workflows/tests.yml)
[![release](https://img.shields.io/github/v/release/voidforall/fengshui.skill)](https://github.com/voidforall/fengshui.skill/releases)
[![Agent Skills](https://img.shields.io/badge/Agent%20Skills-compatible-8a2be2)](https://agentskills.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**让你的 AI 智能体变成一位懂玄空飞星、八宅、择日与八字的传统顾问。**
排盘由代码算，解读由模型说，每条说法都能查到出处。可在 Claude Code、Codex CLI 等 30+ 支持 [Agent Skills](https://agentskills.io) 的智能体中使用。

<p align="center">
  <img src="docs/images/feixing-cast.gif" alt="交互飞星盘：点「起盘」，九星按洛书轨迹逐宫飞布，右侧批注随宫位更新" width="720">
</p>

## 能做什么

| | 你可以这样问 | 你会得到 |
|---|---|---|
| **看宅** | 「我家坐北朝南，2018 年入住，最近财运不好，帮我看看」 | 玄空飞星盘、八宅吉方、布局建议，以及可「起盘」的交互盘面 |
| **择日** | 「打算 6 月搬家，帮我选入宅吉日，我 1988 年男，门朝东」 | 排除月破、冲煞后的候选日，附理由 |
| **八字** | 「1990 年 6 月 1 日早上 8 点半北京出生，女，五行缺什么？今年怎样？」 | 先白话、后专业的解读，以及不懂命理也看得懂的交互命盘 |
| **城市五行** | 「给上海主城区做一张五行地图」 | 覆盖整个声明范围的着色地图，每块都有分类理由、来源与置信度 |
| **问答** | 「『山上龙神不下水』是什么意思？」 | 引原文、注出处的解释 |

用英文提问时用英文作答，盘面与地图也生成英文版；术语按统一的中英对照表，有国际或国家标准译名的按标准取。

## 安装

```bash
npx skills add voidforall/fengshui.skill --skill fengshui-master   # 风水：看宅、择日、问答
npx skills add voidforall/fengshui.skill --skill bazi-mingli       # 八字
npx skills add voidforall/fengshui.skill --skill city-wuxing-map   # 城市五行地图
```

不带 `--skill` 时会列出三个 skill 让你勾选（`--skill '*'` 全装）。装好后直接用自然语言提问，不需要记任何指令。

## 效果

<table>
  <tr>
    <td width="50%"><a href="docs/examples/bazi-demo.html"><img src="docs/images/bazi-chart.png" alt="交互八字命盘：一眼看懂的白话总结，下方四柱卡片带十神白话释义与合冲刑害弧线"></a></td>
    <td width="50%"><a href="docs/examples/london-wuxing.html"><img src="docs/images/london-wuxing.png" alt="伦敦全城五行地图"></a></td>
  </tr>
  <tr>
    <td align="center"><b>八字命盘</b>：白话总结在前，术语都能点开看解释</td>
    <td align="center"><b>城市五行地图</b>：<a href="docs/examples/london-wuxing.html">伦敦</a>、<a href="docs/examples/new-york-wuxing.html">纽约</a>全城，<a href="docs/examples/shanghai-wuxing.html">上海</a>主城区</td>
  </tr>
</table>

所有盘面都是单个 HTML 文件，离线可开，手机与深色模式都能看。示例见 [docs/examples](docs/examples/)。

## 为什么可信

- **计算交给代码，解读交给模型。** 大模型不擅长排盘、推节气，这类错误「看起来对」，最难发现。所有排盘、历法、查表都由确定性脚本完成，并有回归测试。
- **说法要有出处。** 每条规则、引文都标明出处与核对状态，不把通行做法说成经典原文。
- **不恐吓，不卖摆件。** 风水为辅，人为为主；只说倾向，不说「命中注定」。

想知道背后怎么算，见[工作原理](docs/how-it-works.md)。

## 参考典籍

| 方向 | 典籍 |
|------|------|
| 风水 | 《宅经》《葬书》《青囊序》《天玉经》《撼龙经》《周易·说卦传》《沈氏玄空学》《八宅明镜》《协纪辨方书》《地理五诀》《紫白诀》 |
| 城市五行 | 《尚书·洪范》《五行大义》 |
| 八字 | 《三命通会》《渊海子平》《穷通宝鉴》《滴天髓阐微》《五行大义》 |

## 路线图

- [x] 飞星揭盘：二十四山罗盘、九宫逐宫飞布、点宫看批注
- [x] 八字命盘：白话总结、术语解释、合冲刑害、大运流年拖动
- [x] 城市五行地图：伦敦、纽约全城，上海主城区
- [x] 英文版：英文作答、英文盘面与地图
- [ ] 罗盘定向：手机陀螺仪对准大门，实时显示坐向
- [ ] 户型对位：把房间拖到九宫，逐间看吉凶
- [ ] 择日月历、八宅方位图、起卦

## 文档

- 各 skill 的规则与流程：[fengshui-master](skills/fengshui-master/SKILL.md) · [bazi-mingli](skills/bazi-mingli/SKILL.md) · [city-wuxing-map](skills/city-wuxing-map/SKILL.md)
- 完整对话示例：[看宅](skills/fengshui-master/examples/yangzhai.md) · [择日](skills/fengshui-master/examples/zeri-example.md)
- [工作原理](docs/how-it-works.md)：skill 如何分工、各项按什么口径计算
- [参与贡献](CONTRIBUTING.md)（勘误、测试、发版）· [变更记录](CHANGELOG.md)
- 发现错误？欢迎提 issue，请附出处（典籍卷次或可核对的资料）。

## 许可

代码与文档以 [MIT](LICENSE) 发布。城市地图用到的第三方数据与 Leaflet 保留各自的许可，见[数据源说明](skills/city-wuxing-map/examples/sources/README.md)。

## 免责声明

本项目基于传统堪舆与命理典籍，仅供学习、参考与文化探讨。重大居住与人生决策请结合实际情况，勿作为唯一依据。

## Star History

<a href="https://www.star-history.com/#voidforall/fengshui.skill&Date">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=voidforall/fengshui.skill&type=Date&theme=dark" />
    <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=voidforall/fengshui.skill&type=Date" />
    <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=voidforall/fengshui.skill&type=Date" />
  </picture>
</a>
