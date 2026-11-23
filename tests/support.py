"""测试公共设置：把计算包源头 lib/ 加入 import 路径，登记各 skill 的模板目录，并提供历法依赖的跳过标记。

各测试文件第一行 `import support` 即可。
"""

import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LIB = os.path.join(ROOT, "lib")
SKILLS = os.path.join(ROOT, "skills")
FENGSHUI = os.path.join(SKILLS, "fengshui-master")
BAZI = os.path.join(SKILLS, "bazi-mingli")
GOLDEN = os.path.join(os.path.dirname(__file__), "golden")
if LIB not in sys.path:
    sys.path.insert(0, LIB)

from kanyu import pages  # noqa: E402
from kanyu.almanac import HAS_LUNAR  # noqa: E402

for _skill in (FENGSHUI, BAZI):
    _d = os.path.join(_skill, "assets", "templates")
    if _d not in pages.TEMPLATE_DIRS:
        pages.TEMPLATE_DIRS.append(_d)

needs_lunar = unittest.skipUnless(HAS_LUNAR, "需要 lunar_python")
