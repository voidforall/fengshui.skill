#!/usr/bin/env python3
"""堪舆确定性计算工具入口。实现见 scripts/kanyu/，用法：python3 scripts/fengshui.py -h"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kanyu.cli import main  # noqa: E402

if __name__ == "__main__":
    main()
