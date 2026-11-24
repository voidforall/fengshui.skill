"""kanyu —— 堪舆确定性计算。

模块划分：
  公共        core（干支、二十四山、九宫、元运，纯标准库）、almanac（历法、真太阳时，依赖 lunar_python 可选）、
              bazhai（八宅：命卦、游年）、cli（命令行公共部分）、pages（HTML 页面公共部分）
  风水        feixing（玄空飞星）、zibai（流年流月紫白、年家煞方）、zeri（择日）、
              render（文字输出）、pages_feixing（飞星盘）、cli_fengshui（fengshui.py 的命令）
  八字        ganzhi（干支查表）、bazi（八字排盘）、glossary（术语白话）、data/（《穷通宝鉴》索引）、
              render_bazi（文字输出）、pages_bazi（命盘）、cli_bazi（bazi.py 的命令）

本包（仓库 lib/kanyu/）由 tools/sync_kanyu.py 复制到各 skill 的 scripts/kanyu/：
fengshui-master 带公共 + 风水模块，bazi-mingli 带公共 + 八字模块。只改这里；风水与八字模块互不导入。

计算函数只返回数据（dataclass / dict），不做格式化；格式化在 render / render_bazi。
"""

__version__ = "3.2.1"
