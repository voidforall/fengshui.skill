"""干支规则表（八字、流年共用）。纯标准库，只做查表，不判定旺衰、用神、吉凶。

出处与核对状态见 references/sources.md「三、干支关系」「八、八字查表」。
"""

from __future__ import annotations

from .core import GAN, ZHI, JIAZI, wuxing_of

PILLAR_NAMES = ("年", "月", "日", "时")

# --- 藏干（通行表：本气、中气、余气）⚖ ----------------------------------------------
# 与 lunar-python 一致（tests/test_ganzhi.py）。《三命通会》「论人元司事」所列略异（如亥中有戊）。
HIDE_GAN = {
    "子": "癸", "丑": "己癸辛", "寅": "甲丙戊", "卯": "乙", "辰": "戊乙癸", "巳": "丙庚戊",
    "午": "丁己", "未": "己丁乙", "申": "庚壬戊", "酉": "辛", "戌": "戊辛丁", "亥": "壬甲",
}
QI_NAMES = ("本气", "中气", "余气")

# --- 纳音 🧮 与 lunar-python 60 甲子逐一一致（tests/test_ganzhi.py）；每两甲子一名，自甲子起 ---------------
_NAYIN_NAMES = ("海中金 炉中火 大林木 路旁土 剑锋金 山头火 涧下水 城头土 白蜡金 杨柳木 泉中水 屋上土 霹雳火 松柏木 长流水 "
                "沙中金 山下火 平地木 壁上土 金箔金 覆灯火 天河水 大驿土 钗钏金 桑柘木 大溪水 沙中土 天上火 石榴木 大海水").split()
NAYIN = {gz: _NAYIN_NAMES[i // 2] for i, gz in enumerate(JIAZI)}

# --- 十神 -------------------------------------------------------------------------

_SHENG = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}   # 我生
_KE = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}      # 我克


def is_yang(ch: str) -> bool:
    return (GAN.index(ch) if ch in GAN else ZHI.index(ch)) % 2 == 0


def shishen(day_gan: str, other: str) -> str:
    """other（天干）对日干的十神。同阴阳为偏（比肩、食神、偏财、七杀、偏印）。"""
    a, b = wuxing_of(day_gan), wuxing_of(other)
    same = is_yang(day_gan) == is_yang(other)
    if a == b:
        return "比肩" if same else "劫财"
    if _SHENG[a] == b:
        return "食神" if same else "伤官"
    if _KE[a] == b:
        return "偏财" if same else "正财"
    if _KE[b] == a:
        return "七杀" if same else "正官"
    return "偏印" if same else "正印"


# --- 十二长生 ✅《三命通会》卷二「论天干阴阳生死」「论五行旺相休囚死并寄生十二宫」 --------
# 阳干顺行、阴干逆行（「阳生阴死，阳死阴生」）；戊随丙、己随丁（火土同宫）。
CHANGSHENG = ("长生", "沐浴", "冠带", "临官", "帝旺", "衰", "病", "死", "墓", "绝", "胎", "养")
_SHENG_AT = dict(zip(GAN, "亥午寅酉寅酉巳子申卯"))


def changsheng(gan: str, zhi: str) -> str:
    start = ZHI.index(_SHENG_AT[gan])
    k = (ZHI.index(zhi) - start) % 12 if is_yang(gan) else (start - ZHI.index(zhi)) % 12
    return CHANGSHENG[k]


# --- 月令人元司事 ✅《三命通会》卷二「论人元司事」 ------------------------------------------
# 交节后依次用事的天数；原文寅作「艮土」、申作「坤土」，照录。
SILING = {
    "寅": (("艮土", 5), ("丙火", 5), ("甲木", 20)),
    "卯": (("甲木", 7), ("乙木", 23)),
    "辰": (("乙木", 7), ("壬水", 5), ("戊土", 18)),
    "巳": (("戊土", 7), ("庚金", 5), ("丙火", 18)),
    "午": (("丙火", 7), ("丁火", 23)),
    "未": (("丁火", 7), ("甲木", 5), ("己土", 18)),
    "申": (("坤土", 5), ("壬水", 5), ("庚金", 20)),
    "酉": (("庚金", 7), ("辛金", 23)),
    "戌": (("辛金", 7), ("丙火", 5), ("戊土", 18)),
    "亥": (("戊土", 5), ("甲木", 5), ("壬水", 20)),
    "子": (("壬水", 7), ("癸水", 23)),
    "丑": (("癸水", 7), ("庚金", 5), ("己土", 18)),
}


def siling(month_zhi: str, day_n: int) -> str:
    """交节后第 day_n 日（从 1 起）司令之神；超过 30 日仍归末一神。"""
    acc = 0
    for name, days in SILING[month_zhi]:
        acc += days
        if day_n <= acc:
            return name
    return SILING[month_zhi][-1][0]


# --- 干支关系 ✅《三命通会》卷二（论十干合、论支元六合、论支元三合、论六害、论三刑、论冲击）--------

GAN_HE = {frozenset("甲己"), frozenset("乙庚"), frozenset("丙辛"), frozenset("丁壬"), frozenset("戊癸")}
LIUHE = {frozenset(p) for p in ("子丑", "寅亥", "卯戌", "辰酉", "巳申", "午未")}
LIUHAI = {frozenset(p) for p in ("子未", "丑午", "寅巳", "卯辰", "申亥", "酉戌")}
# 三刑按原文两两相刑：寅刑巳、巳刑申、申刑寅；丑刑戌、戌刑未、未刑丑；子卯相刑；辰午酉亥自刑
XING = {frozenset(p): n for ps, n in (("寅巳 巳申 申寅", "无恩之刑"), ("丑戌 戌未 未丑", "恃势之刑"),
                                      ("子卯", "无礼之刑")) for p in ps.split()}
ZIXING = set("辰午酉亥")
SANHE = {"申子辰": "水", "亥卯未": "木", "寅午戌": "火", "巳酉丑": "金"}
SANHUI = {"寅卯辰": "木", "巳午未": "火", "申酉戌": "金", "亥子丑": "水"}   # 渊海子平「一气」


def chong(a: str, b: str) -> bool:
    return (ZHI.index(a) - ZHI.index(b)) % 12 == 6


def pair_relations(a: str, b: str) -> list[str]:
    """两支（或两干）之间的关系名。"""
    if a in GAN:
        return ["合"] if frozenset((a, b)) in GAN_HE else []
    out = []
    if frozenset((a, b)) in LIUHE:
        out.append("六合")
    if chong(a, b):
        out.append("冲")
    if a == b and a in ZIXING:
        out.append("自刑")
    elif frozenset((a, b)) in XING:
        out.append("刑")
    if frozenset((a, b)) in LIUHAI:
        out.append("害")
    return out


def relations(items: list[tuple[str, str]]) -> list[dict]:
    """items：[(位置名, 干或支)]，同为天干或同为地支。返回两两关系与三合、三会。

    三合三字全见才成局；只见两字时标「三合缺一」，按《三命通会》「若三字缺一则化不成局」不作化局。
    """
    out = []
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            (pa, a), (pb, b) = items[i], items[j]
            for r in pair_relations(a, b):
                out.append({"kind": r, "members": [pa, pb], "chars": a + b})
    if items and items[0][1] in ZHI:
        present = {}
        for pos, z in items:
            present.setdefault(z, []).append(pos)
        for table, kind in ((SANHE, "三合"), (SANHUI, "三会")):
            for trio, wx in table.items():
                hit = [z for z in trio if z in present]
                if len(hit) == 3:
                    out.append({"kind": kind, "members": [present[z][0] for z in trio], "chars": trio,
                                "wuxing": wx})
                elif kind == "三合" and len(hit) == 2:
                    out.append({"kind": "三合缺一", "members": [present[z][0] for z in hit],
                                "chars": "".join(hit), "wuxing": wx, "missing": next(z for z in trio if z not in present)})
    return out


def relation_label(r: dict) -> str:
    """如「月支巳、日支亥 冲」「申子辰 三合水局」。"""
    if r["kind"] == "三合":
        return f"{r['chars']}三合{r['wuxing']}局（{'、'.join(r['members'])}）"
    if r["kind"] == "三会":
        return f"{r['chars']}三会{r['wuxing']}方（{'、'.join(r['members'])}）"
    if r["kind"] == "三合缺一":
        return f"{r['chars']}（{'、'.join(r['members'])}）三合缺{r['missing']}，不成局"
    kind = {"合": "合", "六合": "六合", "冲": "冲", "刑": XING.get(frozenset(r["chars"]), "刑"),
            "自刑": "自刑", "害": "害"}[r["kind"]]
    return f"{r['members'][0]}{r['chars'][0]}、{r['members'][1]}{r['chars'][1]} {kind}"


# --- 旬空 ✅《三命通会》卷三「论空亡」：甲子旬无戌亥，余仿此 ------------------------------

def xunkong(gz: str) -> str:
    """所在旬的空亡二支。"""
    i = JIAZI.index(gz)
    first = i - i % 10
    zi = ZHI.index(JIAZI[first][1])
    return ZHI[(zi + 10) % 12] + ZHI[(zi + 11) % 12]


# --- 查表神煞 ✅《三命通会》卷二「论咸池」、卷三「论十干禄」「论羊刃」「论天乙贵人」「论驿马」 ---------

LU = dict(zip(GAN, "寅卯巳午巳午申酉亥子"))
YANGREN = {"甲": "卯", "丙": "午", "戊": "午", "庚": "酉", "壬": "子"}   # 子平：五阳干有刃
TIANYI = {**dict.fromkeys("甲戊庚", "丑未"), **dict.fromkeys("乙己", "子申"),
          **dict.fromkeys("丙丁", "亥酉"), **dict.fromkeys("壬癸", "卯巳"), "辛": "寅午"}
_SANHE_OF = {z: trio for trio in SANHE for z in trio}
YIMA = {"申子辰": "寅", "寅午戌": "申", "巳酉丑": "亥", "亥卯未": "巳"}
XIANCHI = {"申子辰": "酉", "寅午戌": "卯", "巳酉丑": "午", "亥卯未": "子"}


def shensha(pillars: list[str]) -> list[dict]:
    """原局查表神煞：{name, basis, targets（应在之支）, hits（四柱中见于何柱）}。

    只列「柱中见到」的；未见者不列。神煞名目只作查表事实，不单独据以论吉凶。
    """
    stems = [p[0] for p in pillars]
    zhis = [p[1] for p in pillars]
    names = PILLAR_NAMES[:len(pillars)]
    rules = [
        ("禄", f"日干{stems[2]}", LU[stems[2]]),
        ("羊刃", f"日干{stems[2]}", YANGREN.get(stems[2], "")),
        ("天乙贵人", f"日干{stems[2]}", TIANYI[stems[2]]),
        ("天乙贵人", f"年干{stems[0]}", TIANYI[stems[0]]),
        ("驿马", f"年支{zhis[0]}", YIMA[_SANHE_OF[zhis[0]]]),
        ("驿马", f"日支{zhis[2]}", YIMA[_SANHE_OF[zhis[2]]]),
        ("咸池（桃花）", f"年支{zhis[0]}", XIANCHI[_SANHE_OF[zhis[0]]]),
        ("咸池（桃花）", f"日支{zhis[2]}", XIANCHI[_SANHE_OF[zhis[2]]]),
        ("空亡", f"日柱{pillars[2]}旬", xunkong(pillars[2])),
        ("空亡", f"年柱{pillars[0]}旬", xunkong(pillars[0])),
    ]
    out = []
    for name, basis, targets in rules:
        if not targets:
            continue
        hits = [f"{n}支{z}" for n, z in zip(names, zhis) if z in targets]
        if hits:
            out.append({"name": name, "basis": basis, "targets": targets, "hits": hits})
    return out


def against_natal_items(gz: str, natal: list[str]) -> list[dict]:
    """大运或流年干支 gz 与原局各柱的关系（干合；支六合、冲、刑、害；与原局两支凑成三合、三会）。

    每项 {kind, side: 干|支, char, with: [(柱名, 字), ...], wuxing?}；文字由 against_natal 或页面按语言生成。
    """
    names = PILLAR_NAMES[:len(natal)]
    out = []
    g, z = gz
    for n, p in zip(names, natal):
        if frozenset((g, p[0])) in GAN_HE:
            out.append({"kind": "合", "side": "干", "char": g, "with": [(n, p[0])]})
    for n, p in zip(names, natal):
        for r in pair_relations(z, p[1]):
            kind = XING.get(frozenset((z, p[1])), "刑") if r == "刑" else r
            out.append({"kind": kind, "side": "支", "char": z, "with": [(n, p[1])]})
    zhis = {p[1]: n for n, p in zip(names, natal)}
    for table, kind in ((SANHE, "三合"), (SANHUI, "三会")):
        for trio, wx in table.items():
            if z in trio and all(x in zhis for x in trio if x != z) and z not in zhis:
                out.append({"kind": kind, "side": "支", "char": z, "with": [(zhis[x], x) for x in trio if x != z],
                            "wuxing": wx})
    return out


def against_natal(gz: str, natal: list[str], who: str) -> list[str]:
    out = []
    for it in against_natal_items(gz, natal):
        head = f"{who}{it['side']}{it['char']}"
        if it["kind"] in ("三合", "三会"):
            others = "、".join(f"{n}支{x}" for n, x in it["with"])
            out.append(f"{head}与{others}{it['kind']}{it['wuxing']}{'局' if it['kind'] == '三合' else '方'}")
        else:
            (n, x), = it["with"]
            out.append(f"{head}与{n}支{x}自刑" if it["kind"] == "自刑" else f"{head}{it['kind']}{n}{it['side']}{x}")
    return out


# --- 旺相休囚死 ✅《三命通会》卷二：春木旺、夏火旺、六月土旺、秋金旺、冬水旺 ------------------------
# 原文只单列六月（未）为土旺，辰、戌、丑随所在之季。

SEASON_WANG = {**dict.fromkeys("寅卯辰", "木"), **dict.fromkeys("巳午", "火"), "未": "土",
               **dict.fromkeys("申酉戌", "金"), **dict.fromkeys("亥子丑", "水")}
SEASON_NAME = {**dict.fromkeys("寅卯辰", "春"), **dict.fromkeys("巳午", "夏"), "未": "六月",
               **dict.fromkeys("申酉戌", "秋"), **dict.fromkeys("亥子丑", "冬")}


def wangxiang(month_zhi: str) -> dict[str, str]:
    """月令下五行的旺相休囚死：当令为旺，旺者所生为相，生旺者为休，克旺者为囚，旺者所克为死。"""
    w = SEASON_WANG[month_zhi]
    states = {w: "旺", _SHENG[w]: "相", _KE[w]: "死"}
    for x in "木火土金水":
        if _SHENG[x] == w:
            states[x] = "休"
        elif _KE[x] == w:
            states[x] = "囚"
    return {x: states[x] for x in "木火土金水"}


# --- 根气轻重、寒暖燥湿（《滴天髓阐微》，原文已核对，见 references/sources.md） -------------------------
# 「衰旺」任氏：「长生禄旺，根之重者也；墓库余气，根之轻者也。」只列事实，不据此打分定旺衰。
# 「寒暖」原注：「金水为寒，木火为暖。」「燥湿」任注：辰、丑为湿土，未、戌为燥土。

def root_weight(gan: str, zhi: str) -> str:
    """天干在某支（须为其根）的轻重：长生、临官、帝旺或本气同五行为重根；墓库、余气、中气为轻根。"""
    if changsheng(gan, zhi) in ("长生", "临官", "帝旺") or wuxing_of(HIDE_GAN[zhi][0]) == wuxing_of(gan):
        return "重根"
    return "轻根"


WET_EARTH, DRY_EARTH = "辰丑", "未戌"
SEASON_TEMP = {**dict.fromkeys("亥子丑", "冬月，寒"), **dict.fromkeys("巳午", "夏月，暖"), "未": "六月，暖而燥",
               **dict.fromkeys("寅卯辰", "春月"), **dict.fromkeys("申酉戌", "秋月")}


def climate(pillars: list[str]) -> dict:
    """寒暖燥湿的事实：月令季节、水火在何处（干、支本气、支中气余气）、湿土燥土在何处。"""
    names = PILLAR_NAMES
    where = {"火": [], "水": []}
    for n, p in zip(names, pillars):
        for e in where:
            if wuxing_of(p[0]) == e:
                where[e].append(f"{n}干{p[0]}")
            for k, h in enumerate(HIDE_GAN[p[1]]):
                if wuxing_of(h) == e:
                    where[e].append(f"{n}支{p[1]}{QI_NAMES[k]}{h}")
    return {"month": pillars[1][1], "season": SEASON_TEMP[pillars[1][1]], "fire": where["火"], "water": where["水"],
            "wet_earth": [f"{n}支{p[1]}" for n, p in zip(names, pillars) if p[1] in WET_EARTH],
            "dry_earth": [f"{n}支{p[1]}" for n, p in zip(names, pillars) if p[1] in DRY_EARTH]}
