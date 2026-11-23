"""英文术语表：中文术语 → (英文意译, 拼音)。各 skill 的英文作答与英文页面共用这一份。

约定（见各 skill 的 references/english.md）：英文意译在前，第一次出现时附拼音与简体汉字，
如 "Flying Stars (Xuan Kong Fei Xing 玄空飞星)"。拼音不标声调。
修改后运行 python3 tools/sync_kanyu.py，重新生成各 skill 的 references/terms-en.md。
"""

from __future__ import annotations

# --- 公共：五行、干支、八卦、方位 --------------------------------------------------------

ELEMENTS = {"木": "Wood", "火": "Fire", "土": "Earth", "金": "Metal", "水": "Water"}

# 天干：(拼音, 阴阳五行)
GAN = {
    "甲": ("Jia", "Yang Wood"), "乙": ("Yi", "Yin Wood"), "丙": ("Bing", "Yang Fire"), "丁": ("Ding", "Yin Fire"),
    "戊": ("Wu", "Yang Earth"), "己": ("Ji", "Yin Earth"), "庚": ("Geng", "Yang Metal"), "辛": ("Xin", "Yin Metal"),
    "壬": ("Ren", "Yang Water"), "癸": ("Gui", "Yin Water"),
}
# 地支：(拼音, 生肖)
ZHI = {
    "子": ("Zi", "Rat"), "丑": ("Chou", "Ox"), "寅": ("Yin", "Tiger"), "卯": ("Mao", "Rabbit"),
    "辰": ("Chen", "Dragon"), "巳": ("Si", "Snake"), "午": ("Wu", "Horse"), "未": ("Wei", "Goat"),
    "申": ("Shen", "Monkey"), "酉": ("You", "Rooster"), "戌": ("Xu", "Dog"), "亥": ("Hai", "Pig"),
}
# 八卦与中宫：(拼音, 卦象, 方位)
PALACES = {
    "坎": ("Kan", "Water", "North"), "艮": ("Gen", "Mountain", "Northeast"), "震": ("Zhen", "Thunder", "East"),
    "巽": ("Xun", "Wind", "Southeast"), "离": ("Li", "Fire", "South"), "坤": ("Kun", "Earth", "Southwest"),
    "兑": ("Dui", "Lake", "West"), "乾": ("Qian", "Heaven", "Northwest"), "中": ("Zhong", "Center", "Center"),
}
DIRECTIONS = {"北": "North", "东北": "Northeast", "东": "East", "东南": "Southeast", "南": "South",
              "西南": "Southwest", "西": "West", "西北": "Northwest", "中": "Center"}

DIR_ABBR = {"北": "N", "东北": "NE", "东": "E", "东南": "SE", "南": "S", "西南": "SW", "西": "W", "西北": "NW", "中": "C"}


def pinyin(ch: str) -> str:
    """天干、地支、卦名的拼音（二十四山都在其中）。"""
    for table in (GAN, ZHI, PALACES):
        if ch in table:
            return table[ch][0]
    raise KeyError(ch)


COMMON = [
    ("五行", "Five Elements", "Wu Xing"),
    ("阴阳", "Yin and Yang", "Yin Yang"),
    ("相生", "mutual generation", "Xiang Sheng"),
    ("相克", "mutual restraint", "Xiang Ke"),
    ("天干", "Heavenly Stems", "Tian Gan"),
    ("地支", "Earthly Branches", "Di Zhi"),
    ("干支", "Stems and Branches", "Gan Zhi"),
    ("六十甲子", "sixty-year cycle", "Liu Shi Jia Zi"),
    ("生肖", "Chinese Zodiac", "Sheng Xiao"),
    ("八卦", "Eight Trigrams", "Ba Gua"),
    ("节气", "solar terms", "Jie Qi"),
    ("二十四节气", "Twenty-four Solar Terms", "Er Shi Si Jie Qi"),
    ("气", "qi (vital force)", "Qi"),
    ("立春", "Start of Spring", "Li Chun"),
    ("农历", "Chinese lunisolar calendar", "Nong Li"),
    ("闰月", "leap month", "Run Yue"),
    ("真太阳时", "true solar time", "Zhen Tai Yang Shi"),
    ("夏令时", "daylight saving time", "Xia Ling Shi"),
    ("五色", "Five Colors", "Wu Se"),
]

# 有国家级或国际标准译名的术语，按标准取译名，并记下出处与原表述（markdown() 列在表末）。
# CT：中华思想文化术语传播工程 www.chinesethought.cn（国务院批准，外研社）；
# WHO：WHO international standard terminologies on traditional Chinese medicine (2022), ISBN 9789240042322。
# 单个节气名（立春等）、风水与命理专名目前没有国家或国际标准，用通行译法。
STANDARD = {
    "五行": "CT「Wuxing」/ the five elements；WHO 28「Five elements」(synonym: Five phases)",
    "阴阳": "CT「Yin and Yang」；WHO 3「Yin–yang」",
    "相生": "WHO 34「The five elements mutually generate」(synonym: Mutual generation)；CT 4148「each in turn producing the next」",
    "相克": "WHO 35「The five elements mutually restrain」(synonym: Mutual controlling)，名词形式作 mutual restraint；CT 4149「checking」",
    "天干": "WHO 469「Heavenly stems」",
    "地支": "WHO 470「Earthly branches」",
    "六十甲子": "WHO 471「Sixty-year cycle」（亦用于纪月、日、时）",
    "八卦": "CT 2228「Eight Trigrams」",
    "二十四节气": "CT 4058「The Twenty-four Solar Terms」",
    "生肖": "CT 4067「The Chinese Zodiac / Animal of the Year」",
    "气": "CT 2130「Qi (Vital Force)」",
    "五色": "WHO 49「Five colours」，本表用美式拼写 Five Colors",
}

# --- 风水 -------------------------------------------------------------------------------

STARS = {
    1: ("1 White", "Greedy Wolf", "Tan Lang"), 2: ("2 Black", "Giant Door", "Ju Men"),
    3: ("3 Jade", "Salary Preserved", "Lu Cun"), 4: ("4 Green", "Literary Arts", "Wen Qu"),
    5: ("5 Yellow", "Chastity", "Lian Zhen"), 6: ("6 White", "Military Arts", "Wu Qu"),
    7: ("7 Red", "Broken Army", "Po Jun"), 8: ("8 White", "Left Assistant", "Zuo Fu"),
    9: ("9 Purple", "Right Assistant", "You Bi"),
}
YOUNIAN = {
    "生气": ("Life Generating", "Sheng Qi"), "延年": ("Longevity", "Yan Nian"),
    "天医": ("Heavenly Doctor", "Tian Yi"), "伏位": ("Stability", "Fu Wei"),
    "祸害": ("Mishap", "Huo Hai"), "六煞": ("Six Killings", "Liu Sha"),
    "五鬼": ("Five Ghosts", "Wu Gui"), "绝命": ("Total Loss", "Jue Ming"),
}
JIANCHU = {
    "建": "Establish", "除": "Remove", "满": "Full", "平": "Balance", "定": "Stable", "执": "Initiate",
    "破": "Destruction", "危": "Danger", "成": "Success", "收": "Receive", "开": "Open", "闭": "Close",
}
EVENTS = {
    "入宅": "moving into a new home", "搬家": "moving house", "开业": "business opening",
    "动土": "groundbreaking", "装修": "renovation", "嫁娶": "wedding", "订婚": "engagement",
    "安葬": "burial", "出行": "travel", "签约": "signing a contract", "安床": "installing a bed",
}

FENGSHUI = [
    ("风水", "Feng Shui", "Feng Shui"),
    ("堪舆", "Chinese geomancy", "Kan Yu"),
    ("峦头", "Landform school", "Luan Tou"),
    ("形势", "Form school", "Xing Shi"),
    ("理气", "Qi formulas", "Li Qi"),
    ("龙穴砂水向", "Dragon, Lair, Sand, Water and Facing", "Long Xue Sha Shui Xiang"),
    ("玄空飞星", "Flying Stars", "Xuan Kong Fei Xing"),
    ("三元九运", "Three Cycles and Nine Periods", "San Yuan Jiu Yun"),
    ("元运", "Period", "Yuan Yun"),
    ("九运", "Period 9 (2024–2043)", "Jiu Yun"),
    ("运盘", "Period Chart (base stars)", "Yun Pan"),
    ("山星", "Mountain Star", "Shan Xing"),
    ("向星", "Facing Star (Water Star)", "Xiang Xing"),
    ("运星", "Period Star", "Yun Xing"),
    ("流年", "Annual Star", "Liu Nian"),
    ("流月", "Monthly Star", "Liu Yue"),
    ("九宫", "Nine Palaces", "Jiu Gong"),
    ("洛书", "Lo Shu square", "Luo Shu"),
    ("中宫", "Center Palace", "Zhong Gong"),
    ("坐向", "Sitting and Facing directions", "Zuo Xiang"),
    ("坐山", "Sitting direction", "Zuo Shan"),
    ("向首", "Facing direction", "Xiang Shou"),
    ("二十四山", "24 Mountains", "Er Shi Si Shan"),
    ("地元龙", "Earth Dragon sector", "Di Yuan Long"),
    ("天元龙", "Heaven Dragon sector", "Tian Yuan Long"),
    ("人元龙", "Man Dragon sector", "Ren Yuan Long"),
    ("下卦", "Standard Chart", "Xia Gua"),
    ("替卦", "Replacement Chart", "Ti Gua"),
    ("兼向", "Mixed facing (between two mountains)", "Jian Xiang"),
    ("空亡", "Void line", "Kong Wang"),
    ("旺山旺向", "Prosperous Mountain, Prosperous Facing", "Wang Shan Wang Xiang"),
    ("上山下水", "Reversed Mountain and Water", "Shang Shan Xia Shui"),
    ("双星到向", "Double Stars at Facing", "Shuang Xing Dao Xiang"),
    ("双星到坐", "Double Stars at Sitting", "Shuang Xing Dao Zuo"),
    ("伏吟", "Repeating Stars (same as the Lo Shu)", "Fu Yin"),
    ("反吟", "Opposing Stars (reverse of the Lo Shu)", "Fan Yin"),
    ("合十", "Combination of Ten", "He Shi"),
    ("父母三般卦", "Parent String (147/258/369)", "Fu Mu San Ban Gua"),
    ("连珠三般卦", "Continuous Pearl String", "Lian Zhu San Ban Gua"),
    ("当令旺星", "timely (prosperous) star", "Dang Ling Wang Xing"),
    ("生气", "growing star (prosperous next period)", "Sheng Qi"),
    ("次生气", "secondary growing star (prosperous in two periods)", "Ci Sheng Qi"),
    ("退气", "retreating star", "Tui Qi"),
    ("衰气", "declining star", "Shuai Qi"),
    ("死气", "dormant star", "Si Qi"),
    ("五黄煞", "5 Yellow affliction", "Wu Huang Sha"),
    ("五黄", "5 Yellow", "Wu Huang"),
    ("二五交加", "2 Black and 5 Yellow together", "Er Wu Jiao Jia"),
    ("八宅", "Eight Mansions", "Ba Zhai"),
    ("命卦", "Kua number (personal trigram)", "Ming Gua"),
    ("宅卦", "House trigram", "Zhai Gua"),
    ("东四命", "East Group person", "Dong Si Ming"),
    ("西四命", "West Group person", "Xi Si Ming"),
    ("东四宅", "East Group house", "Dong Si Zhai"),
    ("西四宅", "West Group house", "Xi Si Zhai"),
    ("游年", "Eight Wandering Stars (four good, four bad directions)", "You Nian"),
    ("紫白", "Purple-White annual stars", "Zi Bai"),
    ("太岁", "Grand Duke (Tai Sui)", "Tai Sui"),
    ("岁破", "Year Breaker", "Sui Po"),
    ("三煞", "Three Killings", "San Sha"),
    ("择日", "date selection", "Ze Ri"),
    ("建除十二神", "Twelve Day Officers", "Jian Chu Shi Er Shen"),
    ("黄道", "Yellow Path (auspicious) day", "Huang Dao"),
    ("黑道", "Black Path (inauspicious) day", "Hei Dao"),
    ("月破", "Month Breaker day", "Yue Po"),
    ("正四废", "Four Wasted Days", "Zheng Si Fei"),
    ("受死", "Receive Death day (almanac custom)", "Shou Si"),
    ("岁破日", "Year Breaker day (almanac custom)", "Sui Po Ri"),
    ("冲", "clash", "Chong"),
    ("宜", "suitable for", "Yi"),
    ("忌", "avoid", "Ji"),
    ("神煞", "auspicious and inauspicious spirits", "Shen Sha"),
    ("路冲", "road pointing straight at the house", "Lu Chong"),
    ("天斩", "Heaven's Cut (narrow gap between buildings)", "Tian Zhan"),
    ("壁刀", "Wall Blade (building edge pointing at the house)", "Bi Dao"),
    ("反弓", "Reverse Bow (road or river curving away)", "Fan Gong"),
]

# 二十四节气：通行英文名（单个节气名尚无国家或国际标准，见 STANDARD 注）
JIEQI = {
    "立春": "Start of Spring", "雨水": "Rain Water", "惊蛰": "Awakening of Insects", "春分": "Spring Equinox",
    "清明": "Pure Brightness", "谷雨": "Grain Rain", "立夏": "Start of Summer", "小满": "Grain Buds",
    "芒种": "Grain in Ear", "夏至": "Summer Solstice", "小暑": "Minor Heat", "大暑": "Major Heat",
    "立秋": "Start of Autumn", "处暑": "End of Heat", "白露": "White Dew", "秋分": "Autumn Equinox",
    "寒露": "Cold Dew", "霜降": "Frost's Descent", "立冬": "Start of Winter", "小雪": "Minor Snow",
    "大雪": "Major Snow", "冬至": "Winter Solstice", "小寒": "Minor Cold", "大寒": "Major Cold",
}

# --- 八字 -------------------------------------------------------------------------------

SHISHEN = {
    "比肩": ("Friend", "Bi Jian"), "劫财": ("Rob Wealth", "Jie Cai"),
    "食神": ("Eating God", "Shi Shen"), "伤官": ("Hurting Officer", "Shang Guan"),
    "偏财": ("Indirect Wealth", "Pian Cai"), "正财": ("Direct Wealth", "Zheng Cai"),
    "七杀": ("Seven Killings", "Qi Sha"), "正官": ("Direct Officer", "Zheng Guan"),
    "偏印": ("Indirect Resource", "Pian Yin"), "正印": ("Direct Resource", "Zheng Yin"),
}
# 十二长生：(英文名, 白话) —— 白话不用 Death 之类字眼吓人，与中文版一致
CHANGSHENG = {
    "长生": ("Birth", "growing"), "沐浴": ("Bath", "tender and easily hurt"),
    "冠带": ("Crown and Belt", "maturing"), "临官": ("Coming of Age", "established"),
    "帝旺": ("Peak", "at its strongest"), "衰": ("Decline", "starting to wane"),
    "病": ("Sickness", "weakening"), "死": ("Death", "at its weakest"),
    "墓": ("Tomb", "stored away"), "绝": ("Extinction", "empty, awaiting renewal"),
    "胎": ("Conception", "sprouting"), "养": ("Nurture", "taking shape"),
}
# 纳音：六十甲子的物象五行（意译）
NAYIN = {
    "海中金": "Gold in the Sea", "炉中火": "Furnace Fire", "大林木": "Great Forest Wood", "路旁土": "Roadside Earth",
    "剑锋金": "Sword-edge Metal", "山头火": "Mountaintop Fire", "涧下水": "Valley Stream Water", "城头土": "City-wall Earth",
    "白蜡金": "White Wax Metal", "杨柳木": "Willow Wood", "泉中水": "Spring Water", "屋上土": "Rooftop Earth",
    "霹雳火": "Thunderbolt Fire", "松柏木": "Pine and Cypress Wood", "长流水": "Long River Water",
    "沙中金": "Gold in the Sand", "山下火": "Fire below the Mountain", "平地木": "Flatland Wood", "壁上土": "Wall Earth",
    "金箔金": "Gold Leaf Metal", "覆灯火": "Lamp Fire", "天河水": "Heavenly River Water", "大驿土": "Post-road Earth",
    "钗钏金": "Hairpin Metal", "桑柘木": "Mulberry Wood", "大溪水": "Great Stream Water", "沙中土": "Earth in the Sand",
    "天上火": "Fire in the Sky", "石榴木": "Pomegranate Wood", "大海水": "Great Sea Water",
}
PILLARS = {"年": "Year", "月": "Month", "日": "Day", "时": "Hour"}
SEASONS = {"春": "spring", "夏": "summer", "六月": "the sixth month (late summer)", "秋": "autumn", "冬": "winter"}
QI = {"本气": "main qi", "中气": "middle qi", "余气": "residual qi"}
# 相刑的三种名目（《三命通会》）与自刑
XING_KINDS = {"无恩之刑": "ungrateful punishment", "恃势之刑": "bullying punishment",
              "无礼之刑": "uncivil punishment", "自刑": "self-punishment"}

WANGXIANG = {"旺": "Prosperous", "相": "Strong", "休": "Resting", "囚": "Trapped", "死": "Dead (weakest)"}

BAZI = [
    ("八字", "Bazi (Eight Characters)", "Ba Zi"),
    ("四柱", "Four Pillars", "Si Zhu"),
    ("年柱", "Year Pillar", "Nian Zhu"),
    ("月柱", "Month Pillar", "Yue Zhu"),
    ("日柱", "Day Pillar", "Ri Zhu"),
    ("时柱", "Hour Pillar", "Shi Zhu"),
    ("日主", "Day Master", "Ri Zhu"),
    ("天干地支", "Heavenly Stems and Earthly Branches", "Tian Gan Di Zhi"),
    ("十神", "Ten Gods", "Shi Shen"),
    ("藏干", "Hidden Stems", "Cang Gan"),
    ("本气", "main qi", "Ben Qi"),
    ("中气", "middle qi", "Zhong Qi"),
    ("余气", "residual qi", "Yu Qi"),
    ("通根", "rooted (stem has a root in a branch)", "Tong Gen"),
    ("透干", "revealed (hidden stem appears as a stem)", "Tou Gan"),
    ("月令", "Month Command", "Yue Ling"),
    ("司令", "ruling qi of the month", "Si Ling"),
    ("旺相休囚死", "Prosperous, Strong, Resting, Trapped, Dead", "Wang Xiang Xiu Qiu Si"),
    ("十二长生", "Twelve Life Stages", "Shi Er Chang Sheng"),
    ("合", "combination", "He"),
    ("六合", "Six Harmonies", "Liu He"),
    ("三合", "Three Harmony combination", "San He"),
    ("三会", "Directional combination", "San Hui"),
    ("三合缺一", "incomplete Three Harmony (one branch missing)", "San He Que Yi"),
    ("冲", "clash", "Chong"),
    ("刑", "punishment", "Xing"),
    ("害", "harm", "Hai"),
    ("空亡", "Void (empty branches of the decade)", "Kong Wang"),
    ("禄", "Prosperity (Lu)", "Lu"),
    ("羊刃", "Goat Blade", "Yang Ren"),
    ("天乙贵人", "Nobleman star", "Tian Yi Gui Ren"),
    ("驿马", "Travelling Horse", "Yi Ma"),
    ("咸池", "Peach Blossom", "Xian Chi"),
    ("纳音", "Na Yin (sound element of a pillar)", "Na Yin"),
    ("起运", "start of the Luck Pillars", "Qi Yun"),
    ("大运", "Luck Pillar (ten-year period)", "Da Yun"),
    ("流年", "Annual Pillar", "Liu Nian"),
    ("调候", "climate adjustment", "Tiao Hou"),
    ("格局", "chart structure", "Ge Ju"),
    ("从格", "Follow structure", "Cong Ge"),
    ("用神", "Useful God (most helpful element)", "Yong Shen"),
    ("喜神", "favorable element", "Xi Shen"),
    ("忌神", "unfavorable element", "Ji Shen"),
    ("五行个数", "element count", "Wu Xing Ge Shu"),
    ("子时换日", "day change at the Zi hour (23:00)", "Zi Shi Huan Ri"),
    ("时辰", "two-hour period of the day", "Shi Chen"),
]


def _rows(pairs):
    return [f"| {zh} | {en} | {py} |" for zh, en, py in pairs]


def markdown(domain: str) -> str:
    """生成 references/terms-en.md。domain：fengshui 或 bazi。"""
    out = ["# English terminology / 英文术语表", "",
           "> 由 lib/kanyu/terms_en.py 生成，英文页面与英文作答都用这一份。不要手改本文件。",
           "> 用法见 english.md：英文意译在前，第一次出现时附拼音与简体汉字，如 Day Master (Ri Zhu 日主)。", "",
           "## Five Elements, stems and branches", "",
           "| 中文 | English | Pinyin |", "|------|---------|--------|"]
    out += _rows(COMMON)
    out += [f"| {k} | {v} | {k_py} |" for (k, v), k_py in zip(ELEMENTS.items(), ("Mu", "Huo", "Tu", "Jin", "Shui"))]
    out += ["", "| 天干 | Pinyin | Element |", "|------|--------|---------|"]
    out += [f"| {k} | {p} | {e} |" for k, (p, e) in GAN.items()]
    out += ["", "| 地支 | Pinyin | Animal |", "|------|--------|--------|"]
    out += [f"| {k} | {p} | {a} |" for k, (p, a) in ZHI.items()]
    out += ["", "| 卦 / 宫 | Pinyin | Image | Direction |", "|------|--------|-------|-----------|"]
    out += [f"| {k} | {p} | {i} | {d} |" for k, (p, i, d) in PALACES.items()]
    if domain == "fengshui":
        out += ["", "## Feng Shui", "", "| 中文 | English | Pinyin |", "|------|---------|--------|"]
        out += _rows(FENGSHUI)
        out += ["", "| 九星 | Star | Name | Pinyin |", "|------|------|------|--------|"]
        from .core import STAR_NAMES
        out += [f"| {STAR_NAMES[n]} | {a} | {b} | {c} |" for n, (a, b, c) in STARS.items()]
        out += ["", "| 游年 | English | Pinyin |", "|------|---------|--------|"]
        out += [f"| {k} | {e} | {p} |" for k, (e, p) in YOUNIAN.items()]
        out += ["", "| 建除 | Day Officer |", "|------|-------------|"]
        out += [f"| {k} | {v} |" for k, v in JIANCHU.items()]
        out += ["", "| 择日事项 | English |", "|----------|---------|"]
        out += [f"| {k} | {v} |" for k, v in EVENTS.items()]
    elif domain == "bazi":
        out += ["", "## Bazi", "", "| 中文 | English | Pinyin |", "|------|---------|--------|"]
        out += _rows(BAZI)
        out += ["", "| 十神 | English | Pinyin |", "|------|---------|--------|"]
        out += [f"| {k} | {e} | {p} |" for k, (e, p) in SHISHEN.items()]
        out += ["", "| 十二长生 | English | Plain English |", "|----------|---------|---------------|"]
        out += [f"| {k} | {e} | {g} |" for k, (e, g) in CHANGSHENG.items()]
        out += ["", "| 旺相休囚死 | English |", "|------------|---------|"]
        out += [f"| {k} | {v} |" for k, v in WANGXIANG.items()]
    else:
        raise ValueError("domain 应为 fengshui 或 bazi")
    out += ["", "## Standard renderings / 标准译名出处", "",
            "以下术语按国家级或国际标准取译名。CT＝中华思想文化术语传播工程（chinesethought.cn）；",
            "WHO＝WHO international standard terminologies on traditional Chinese medicine (2022)，数字为条目号。",
            "其余术语（单个节气名、风水与命理专名）目前没有国家或国际标准，用通行译法。", "",
            "| 中文 | English | 出处 |", "|------|---------|------|"]
    en = {zh: e for zh, e, _ in COMMON}
    out += [f"| {k} | {en[k]} | {v} |" for k, v in STANDARD.items()]
    return "\n".join(out) + "\n"
