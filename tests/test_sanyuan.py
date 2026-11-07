"""把公式与古法「三元起例」逐年对照。

古法以 1864 年（上元甲子）为起点，每 60 年一元：
- 命卦（《八宅明镜》）：男命上元甲子起一坎、中元起四巽、下元起七兑，逐年逆行；
  女命上元起五（寄艮）、中元起二坤、下元起八艮，逐年顺行。
- 年紫白（《紫白诀》起年白法）：上元甲子一白、中元甲子四绿、下元甲子七赤入中，逐年逆行。
公式只是古法的简写，两者必须在每一年都一致。
"""

import support  # noqa: F401
import unittest

from kanyu.bazhai import mingua_raw
from kanyu.zibai import annual_center

SHANGYUAN = 1864   # 同治三年甲子，上元甲子


def _step(start: int, k: int, forward: bool) -> int:
    return (start - 1 + (k if forward else -k)) % 9 + 1


def sanyuan(year: int, starts: tuple[int, int, int], forward: bool) -> int:
    off = (year - SHANGYUAN) % 180      # 三元一周 180 年
    yuan, k = divmod(off, 60)
    return _step(starts[yuan], k, forward)


class TestSanyuan(unittest.TestCase):
    YEARS = range(1684, 2224)   # 前后各覆盖三个三元周期

    def test_male_mingua(self):
        for y in self.YEARS:
            self.assertEqual(mingua_raw(y, "m"), sanyuan(y, (1, 4, 7), False), y)

    def test_female_mingua(self):
        for y in self.YEARS:
            self.assertEqual(mingua_raw(y, "f"), sanyuan(y, (5, 2, 8), True), y)

    def test_annual_zibai(self):
        for y in self.YEARS:
            self.assertEqual(annual_center(y), sanyuan(y, (1, 4, 7), False), y)

    def test_jiazi_years(self):
        self.assertEqual([annual_center(y) for y in (1864, 1924, 1984)], [1, 4, 7])


if __name__ == "__main__":
    unittest.main()
