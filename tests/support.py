"""测试公共设置：把 scripts/ 加入 import 路径，并提供历法依赖的跳过标记。

各测试文件第一行 `import support` 即可。
"""

import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCRIPTS = os.path.join(ROOT, "scripts")
GOLDEN = os.path.join(os.path.dirname(__file__), "golden")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

from kanyu.almanac import HAS_LUNAR  # noqa: E402

needs_lunar = unittest.skipUnless(HAS_LUNAR, "需要 lunar_python")
