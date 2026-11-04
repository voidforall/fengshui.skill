"""基础定义：干支、二十四山、九宫、洛书飞泊、元运。纯标准库。"""

from __future__ import annotations

GAN = "甲乙丙丁戊己庚辛壬癸"
ZHI = "子丑寅卯辰巳午未申酉戌亥"
SHENGXIAO = "鼠牛虎兔龙蛇马羊猴鸡狗猪"
WEEKDAYS = "一二三四五六日"

# 二十四山，自壬起顺时针；第 i 山的中心度数 = (345 + 15*i) % 360
MOUNTAINS = "壬子癸丑艮寅甲卯乙辰巽巳丙午丁未坤申庚酉辛戌乾亥"
# 每 3 山一宫
PALACES = ["坎", "艮", "震", "巽", "离", "坤", "兑", "乾"]
PALACE_NUM = {"坎": 1, "坤": 2, "震": 3, "巽": 4, "中": 5, "乾": 6, "兑": 7, "艮": 8, "离": 9}
NUM_PALACE = {v: k for k, v in PALACE_NUM.items()}
PALACE_DIR = {
    "坎": "北", "艮": "东北", "震": "东", "巽": "东南",
    "离": "南", "坤": "西南", "兑": "西", "乾": "西北", "中": "中",
}
YUANLONG = ["地元", "天元", "人元"]  # 每宫三山依次为 地 / 天 / 人 元龙

STAR_NAMES = {
    1: "一白贪狼", 2: "二黑巨门", 3: "三碧禄存", 4: "四绿文曲", 5: "五黄廉贞",
    6: "六白武曲", 7: "七赤破军", 8: "八白左辅", 9: "九紫右弼",
}

# 洛书飞泊路径：中→乾→兑→艮→离→坎→坤→震→巽
LUOSHU_PATH = ["中", "乾", "兑", "艮", "离", "坎", "坤", "震", "巽"]

# 九宫格显示布局（上南下北，传统罗盘图式）
GRID = [["巽", "离", "坤"], ["震", "中", "兑"], ["艮", "坎", "乾"]]

ZHI_DIR = {"子": "北", "丑": "东北", "寅": "东北", "卯": "东", "辰": "东南", "巳": "东南",
           "午": "南", "未": "西南", "申": "西南", "酉": "西", "戌": "西北", "亥": "西北"}

WUXING = {**dict.fromkeys("甲乙寅卯", "木"), **dict.fromkeys("丙丁巳午", "火"),
          **dict.fromkeys("戊己辰戌丑未", "土"), **dict.fromkeys("庚辛申酉", "金"),
          **dict.fromkeys("壬癸亥子", "水")}


# --- 性别 ------------------------------------------------------------------

_MALE = ("m", "male", "男", "男命")
_FEMALE = ("f", "female", "女", "女命")


def parse_gender(g: str) -> str:
    """规范化为 'm' / 'f'。"""
    g = g.strip().lower()
    if g in _MALE:
        return "m"
    if g in _FEMALE:
        return "f"
    raise ValueError("gender 应为 m/f 或 男/女")


# --- 二十四山 ----------------------------------------------------------------

def mountain_index(m: str) -> int:
    i = MOUNTAINS.find(m)
    if i < 0 or len(m) != 1:
        raise ValueError(f"未知山名: {m!r}（应为二十四山之一: {MOUNTAINS}）")
    return i


def mountain_palace(m: str) -> str:
    return PALACES[mountain_index(m) // 3]


def mountain_yuanlong(m: str) -> int:
    """0 地元 / 1 天元 / 2 人元。"""
    return mountain_index(m) % 3


def mountain_yinyang(m: str) -> str:
    """玄空二十四山阴阳（不同于八字地支阴阳）。

    一三七九（坎震兑离）四正宫：地元阳、天元阴、人元阴；
    二四六八（坤巽乾艮）四隅宫：地元阴、天元阳、人元阳。
    """
    pal = mountain_palace(m)
    yl = mountain_yuanlong(m)
    if PALACE_NUM[pal] % 2 == 1:
        return "+" if yl == 0 else "-"
    return "-" if yl == 0 else "+"


def palace_mountain(palace: str, yuanlong: int) -> str:
    """某宫某元龙之山。"""
    return MOUNTAINS[PALACES.index(palace) * 3 + yuanlong]


def opposite(m: str) -> str:
    return MOUNTAINS[(mountain_index(m) + 12) % 24]


def neighbor(m: str, step: int) -> str:
    return MOUNTAINS[(mountain_index(m) + step) % 24]


def mountain_center_deg(m: str) -> float:
    return (345 + 15 * mountain_index(m)) % 360


def deg_to_mountain(deg: float) -> tuple[str, float]:
    """度数 → (所在山, 偏离该山中线的度数，正为顺时针偏)。"""
    deg = deg % 360
    i = int(((deg - 337.5) % 360) // 15)
    m = MOUNTAINS[i]
    off = (deg - mountain_center_deg(m) + 180) % 360 - 180
    return m, off


def parse_direction(s: str) -> tuple[str, float | None]:
    """接受山名（如「子」）或度数（如「182.5」）。返回 (山, 度数或 None)。"""
    s = s.strip().rstrip("°度")
    if len(s) == 1 and s in MOUNTAINS:
        return s, None
    try:
        deg = float(s)
    except ValueError:
        raise ValueError(f"无法识别方向 {s!r}：请给二十四山名或罗盘度数") from None
    return deg_to_mountain(deg)[0], deg % 360


# --- 九宫飞泊 ----------------------------------------------------------------

def fly(center: int, forward: bool = True) -> dict[str, int]:
    """从中宫起 center 星，沿洛书路径顺飞(forward)或逆飞。"""
    out = {}
    for k, pal in enumerate(LUOSHU_PATH):
        step = k if forward else -k
        out[pal] = (center - 1 + step) % 9 + 1
    return out


def palace_of_star(chart: dict[str, int], n: int) -> str:
    return next(p for p, v in chart.items() if v == n)


# --- 年份 / 元运 --------------------------------------------------------------

def ganzhi_of_year(year: int) -> str:
    return GAN[(year - 4) % 10] + ZHI[(year - 4) % 12]


def zhi_of_year(year: int) -> str:
    return ZHI[(year - 4) % 12]


def chong(zhi: str) -> str:
    return ZHI[(ZHI.index(zhi) + 6) % 12]


def shengxiao(zhi: str) -> str:
    return SHENGXIAO[ZHI.index(zhi)]


def yun_of_year(year: int) -> int:
    """三元九运：1864 年起一运，每运 20 年（年份以立春为界）。"""
    return (year - 1864) // 20 % 9 + 1


def yun_range(yun: int) -> tuple[int, int]:
    start = 1864 + (yun - 1) * 20
    return start, start + 19


def wuxing_of(ch: str) -> str:
    return WUXING[ch]
