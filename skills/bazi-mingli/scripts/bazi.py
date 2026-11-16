#!/usr/bin/env python3
"""八字确定性计算工具入口。用法：python3 scripts/bazi.py --birth "YYYY-MM-DD HH:MM" --gender m/f [...]

计算代码 kanyu/ 由仓库根目录 scripts/kanyu/ 同步而来（tools/sync_kanyu.py），不要在此处直接修改。
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kanyu.cli import bazi_main  # noqa: E402

if __name__ == "__main__":
    bazi_main()
