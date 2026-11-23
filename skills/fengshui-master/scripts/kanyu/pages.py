"""可交互 HTML 页面的公共部分：把数据填进模板，生成单个离线可用的 HTML 文件。

各盘面的数据在 pages_feixing.py（飞星盘）与 pages_bazi.py（八字命盘）。
图形与数据全部来自计算模块；模型的解读通过 notes（JSON）传入，只作为文字嵌入页面。
"""

from __future__ import annotations

import json
import os
import re

# 本包随 skill 安装在 <skill>/scripts/kanyu/，模板在 <skill>/assets/templates/。
# 仓库里的源头在 lib/kanyu/，测试时由 tests/support.py 把各 skill 的模板目录加进来。
SKILL_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
TEMPLATE_DIRS = [os.path.join(SKILL_ROOT, "assets", "templates")]


def _embed_json(data) -> str:
    # 防止批注文字中的 </script> 截断脚本
    return json.dumps(data, ensure_ascii=False).replace("</", "<\\/")


def _escape_html(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render(template: str, title: str, data: dict) -> str:
    path = next((os.path.join(d, template) for d in TEMPLATE_DIRS if os.path.exists(os.path.join(d, template))), None)
    if path is None:
        raise FileNotFoundError(f"找不到模板 {template}（查找：{'、'.join(TEMPLATE_DIRS)}）")
    with open(path, encoding="utf-8") as f:
        tpl = f.read()
    return tpl.replace("__TITLE__", _escape_html(title)).replace("__DATA__", _embed_json(data))


def write_page(path: str, html: str) -> str:
    path = os.path.abspath(path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    return path


def extract_data(html: str) -> dict:
    """从生成的页面中取回嵌入的数据（测试用）。"""
    m = re.search(r'<script id="chart-data" type="application/json">(.*?)</script>', html, re.S)
    return json.loads(m.group(1).replace("<\\/", "</"))
