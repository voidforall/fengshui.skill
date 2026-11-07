"""kanyu —— 堪舆确定性计算。

模块划分：
  core      二十四山、九宫、洛书飞泊、元运等基础定义（纯标准库）
  bazhai    八宅：命卦、游年
  feixing   玄空飞星：排盘、格局、兼向
  zibai     流年流月紫白、年家煞方
  almanac   历法：立春分年、节气月、单日信息、真太阳时（依赖 lunar_python，可选）
  zeri      择日筛选规则
  bazi      八字排盘
  render    文字输出
  cli       命令行入口

计算函数只返回数据（dataclass / dict），不做格式化；格式化统一在 render。
"""

__version__ = "2.2.0"
