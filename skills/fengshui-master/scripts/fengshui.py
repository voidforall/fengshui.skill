#!/usr/bin/env python3
"""堪舆确定性计算工具入口。用法：python3 scripts/fengshui.py -h

计算代码 kanyu/ 由仓库的 lib/kanyu/ 同步而来（tools/sync_kanyu.py），不要在此处直接修改。
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kanyu.cli_fengshui import main  # noqa: E402

if __name__ == "__main__":
    main()
