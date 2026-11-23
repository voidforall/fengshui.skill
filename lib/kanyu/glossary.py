"""八字术语的白话释义：交互命盘与 bazi-mingli 的 references/glossary.md 共用这一份。

每条都标出处：✅ 为《三命通会》原文（维基文库本已核对），⚖ 为子平通行释义（无单一经典出处）。
修改后运行 python3 tools/sync_kanyu.py 重新生成 glossary.md。
"""

from __future__ import annotations

SANMING = "《三命通会》"

# 十天干物象 ✅《三命通会》卷二「论天干阴阳生死」
GAN_XIANG = {
    "甲": "在天为雷为龙，在地为梁为栋", "乙": "在天为风，在地为树",
    "丙": "在天为日为电，在地为炉为冶", "丁": "在天为列星，在地为灯火",
    "戊": "在天为雾，在地为山", "己": "乃天之元气，地之真土",
    "庚": "在天为风霜，在地为金铁", "辛": "在天为日月，乃太阴之精，在地为金，金乃山石之矿",
    "壬": "在天为云，在地为泽", "癸": "在天为雨露，在地为泉脉",
}

# 十神：(两三字的白话, 与日主的关系, 通行释义) ⚖ 子平通行释义；关系由生克与阴阳推出
SHISHEN = {
    "比肩": ("同辈", "与日主同五行、同阴阳", "像兄弟朋友、同辈，也代表自我、独立"),
    "劫财": ("竞争", "与日主同五行、阴阳不同", "像竞争的同辈，也代表冲劲、争夺"),
    "食神": ("才华", "日主所生、同阴阳", "才华、口福、温和的表达"),
    "伤官": ("锋芒", "日主所生、阴阳不同", "锋芒、创意、不受拘束的表达"),
    "偏财": ("机会财", "日主所克、同阴阳", "流动的钱财、机会、人缘"),
    "正财": ("稳定财", "日主所克、阴阳不同", "稳定收入、勤劳所得"),
    "七杀": ("压力", "克日主、同阴阳", "压力、挑战，也代表魄力"),
    "正官": ("规矩", "克日主、阴阳不同", "规矩、责任、名誉"),
    "偏印": ("灵感", "生日主、同阴阳", "偏门学问、灵感、独处"),
    "正印": ("庇护", "生日主、阴阳不同", "学习、庇护、长辈的支持"),
}

# 十二长生：(白话, 原文) ✅《三命通会》卷二引《三命提要》；绝即「受气」，胎即「受胎」，养即「成形」
# 白话只描述气势强弱，不用「死」「病」这类字眼吓人；原文照录在第二项。
CHANGSHENG = {
    "长生": ("起步成长", "万物发生向荣，如人始生而向长也"),
    "沐浴": ("稚嫩易损", "万物始生，形体柔脆，易为所损"),
    "冠带": ("渐趋成熟", "万物渐荣秀，如人具衣冠也"),
    "临官": ("自立有成", "万物既秀实，如人之临官也"),
    "帝旺": ("最旺盛", "万物成熟，如人之兴旺也"),
    "衰": ("开始衰退", "万物形衰，如人之气衰也"),
    "病": ("力量减弱", "万物病，如人之病也"),
    "死": ("气势最弱", "万物死，如人之死也"),
    "墓": ("收藏", "万物成功而藏之库，如人之终而归墓也"),
    "绝": ("最空、待重生", "万物在地中未有其象，如母腹空，未有物也"),
    "胎": ("萌芽", "其物在地中萌芽，始有其气，如人受父母之气也"),
    "养": ("孕育成形", "万物在地中成形，如人在母腹成形也"),
}

# 旺相休囚死 ✅《三命通会》卷二「论五行旺相休囚死并寄生十二宫」（「盛德乘时曰旺」）
WANGXIANG = {
    "旺": "当令，这个季节最强的五行",
    "相": "当令者所生，次强",
    "休": "生出当令者，退而休息",
    "囚": "克当令者，反被困住",
    "死": "被当令者所克，最弱",
}

# 术语：(白话, 出处或口径)
TERMS = {
    "日主": ("出生那天的天干，代表你自己。整张盘都围绕它来看：哪些字帮它、哪些字耗它。", "子平法通则"),
    "四柱": ("出生的年、月、日、时各用一对干支表示，共四对八个字，所以叫「八字」。", "子平法通则"),
    "天干地支": ("每柱上面的字叫天干（甲乙丙丁……十个），下面的叫地支（子丑寅卯……十二个），各属五行。", "子平法通则"),
    "十神": ("其他字和日主的关系：生我、我生、克我、我克、同类，再分阴阳，共十种，用来比喻人事。", "子平法通则 ⚖ 释义为通行说法"),
    "藏干": ("地支里面藏着的天干。本气最主要，中气、余气次之。", "通行藏干表 ⚖"),
    "通根": ("天干在地支的藏干里找到同五行的字，好比树有根。根越多、越是本气，站得越稳。", "子平通行看法 ⚖"),
    "透干": ("地支里藏着的字也出现在天干上，力量显露出来。", "子平通行看法 ⚖"),
    "月令": ("出生月份的地支，决定那个季节哪种五行最旺，是判断日主强弱最重要的一项。", "子平法通则"),
    "司令": ("一个月里不同时段轮流当值的字。《三命通会》「论人元司事」列出交节后各几日。", "✅《三命通会》卷二"),
    "旺相休囚死": ("五行随季节的强弱：当令为旺，其次为相，再次休、囚，最弱为死。", "✅《三命通会》卷二"),
    "十二长生": ("日主在每个地支上的状态，古书比作人从出生到归墓的十二个阶段。", "✅《三命通会》卷二；原书言见生旺「未必便作吉论」"),
    "合": ("两字相合、彼此牵绊。《三命通会》：「夫合者，乃和谐之义。」合而化为另一五行要有条件，这里只标合。", "✅《三命通会》卷二"),
    "冲": ("位置正对的两个地支相冲，主变动。原书说「冲破有吉有凶，不可概论」，要看冲的是有利还是不利的字。", "✅《三命通会》卷二"),
    "刑": ("相刑。原书比作「夫妇相合而反致刑伤」，亲近之中带伤。自刑是同一个字重复相见。", "✅《三命通会》卷二"),
    "害": ("相害，原书称「十二支凌战之辰」，彼此妨碍。", "✅《三命通会》卷二"),
    "三合": ("三个地支凑齐，结成一股五行力量（如申子辰成水局）。", "✅《三命通会》卷二"),
    "三会": ("同一方位的三个地支凑齐（如寅卯辰东方木），力量集中。", "✅《渊海子平》"),
    "三合缺一": ("三合只见到两个字，原书说「三字缺一则化不成局」。大运、流年补上第三个字时再看。", "✅《三命通会》卷二"),
    "空亡": ("六十甲子每一旬里轮空的两个地支，古称落空。原书说空亡「未可便为凶论」。", "✅《三命通会》卷三"),
    "禄": ("日干的本位。原书：「禄，爵禄也，当得势而享。」", "✅《三命通会》卷三"),
    "羊刃": ("比禄再进一步的位置，过旺而锋芒太露。原书：「禄过则刃生。」", "✅《三命通会》卷三"),
    "天乙贵人": ("古书最尊贵的吉神，「所至之处，一切凶煞隐然而避」，俗称有贵人相助。", "✅《三命通会》卷三"),
    "驿马": ("主走动、迁移、变化。原书称「喜庆之神」。", "✅《三命通会》卷三"),
    "咸池": ("俗称桃花，主人缘、异性缘。原书断语偏负面，本 skill 不转述，也不据此论品行。", "✅《三命通会》卷二"),
    "纳音": ("六十甲子各配一种五行物象（如路旁土、山下火）的传统名称。", "✅《三命通会》卷一"),
    "起运": ("从几岁几个月开始走第一步大运，由出生到下一个（或上一个）节气的天数推出。", "子平法通则"),
    "大运": ("每十年一换的大环境，像人生的季节。", "子平法通则"),
    "流年": ("每一年的干支，像当年的天气；要和原局、大运一起看。", "子平法通则"),
    "调候": ("按出生季节的冷暖燥湿，看需要什么五行来调和。《穷通宝鉴》专讲这一点。", "✅《穷通宝鉴》"),
    "用神": ("对这张盘最有帮助的五行。这是判断，不同派别可能取得不同，要看依据。", "⚖ 属判断"),
    "喜神": ("对盘有帮助、辅助用神的五行。", "⚖ 属判断"),
    "忌神": ("对盘不利的五行。", "⚖ 属判断"),
    "五行个数": ("八个字里各五行出现的次数。只是字数，不等于强弱，也不等于「缺什么就要补什么」。", "本项目说明"),
}


# --- 英文版（英文命盘用）。原文引文照录中文，附我们的译文（our translation）；白话与中文版逐条对应 ---------
# tests/test_terms_en.py 检查键与中文版一致。

GAN_XIANG_EN = {
    "甲": "in heaven it is thunder and the dragon; on earth, beams and pillars",
    "乙": "in heaven it is wind; on earth, trees",
    "丙": "in heaven it is the sun and lightning; on earth, the furnace and the forge",
    "丁": "in heaven it is the stars; on earth, lamplight",
    "戊": "in heaven it is mist; on earth, mountains",
    "己": "it is the primal qi of heaven and the true soil of earth",
    "庚": "in heaven it is wind and frost; on earth, metal and iron",
    "辛": "in heaven it is the sun and moon, the essence of the great yin; on earth it is metal, the ore in mountain rock",
    "壬": "in heaven it is clouds; on earth, marshes",
    "癸": "in heaven it is rain and dew; on earth, springs and hidden streams",
}

SHISHEN_EN = {
    "比肩": ("peer", "same element and same polarity as the Day Master", "siblings, friends and peers; also selfhood and independence"),
    "劫财": ("rival", "same element as the Day Master, opposite polarity", "competing peers; also drive and contention"),
    "食神": ("talent", "produced by the Day Master, same polarity", "talent, enjoyment of food, gentle self-expression"),
    "伤官": ("sharp edge", "produced by the Day Master, opposite polarity", "brilliance, creativity, unrestrained expression"),
    "偏财": ("windfall wealth", "controlled by the Day Master, same polarity", "money that comes and goes, opportunities, popularity"),
    "正财": ("steady wealth", "controlled by the Day Master, opposite polarity", "steady income, money earned by hard work"),
    "七杀": ("pressure", "controls the Day Master, same polarity", "pressure and challenges; also boldness"),
    "正官": ("rules", "controls the Day Master, opposite polarity", "rules, responsibility, reputation"),
    "偏印": ("inspiration", "produces the Day Master, same polarity", "unconventional learning, inspiration, solitude"),
    "正印": ("support", "produces the Day Master, opposite polarity", "learning, protection, support from elders"),
}

CHANGSHENG_QUOTE_EN = {
    "长生": "all things begin to flourish, like a person just born and starting to grow",
    "沐浴": "things newly born are soft and fragile, easily harmed",
    "冠带": "things grow fine and lush, like a person putting on cap and sash",
    "临官": "things have grown full, like a person taking office",
    "帝旺": "things are ripe, like a person at the height of vigour",
    "衰": "things wane in form, like a person whose vigour declines",
    "病": "things sicken, like a person falling ill",
    "死": "things die, like a person dying",
    "墓": "their work done, things are stored in the vault, like a person returning to the grave",
    "绝": "things in the earth have no form yet, like an empty womb",
    "胎": "things sprout in the earth and first have qi, like a person receiving the qi of father and mother",
    "养": "things take shape in the earth, like a person forming in the mother's womb",
}

WANGXIANG_EN = {
    "旺": "in season: the strongest element this season",
    "相": "produced by the element in season: second strongest",
    "休": "produces the element in season, so it retires to rest",
    "囚": "tries to control the element in season and is trapped instead",
    "死": "controlled by the element in season: the weakest",
}

_SM = "San Ming Tong Hui 三命通会"
TERMS_EN = {
    "日主": ("The stem of your birth day. It stands for you; the whole chart is read around it: which characters help it and which drain it.", "general rule of the Ziping method"),
    "四柱": ("Your birth year, month, day and hour, each written as a stem and a branch: four pairs, eight characters, hence 'Bazi'.", "general rule of the Ziping method"),
    "天干地支": ("The top character of each pillar is a Heavenly Stem (ten of them: Jia, Yi, Bing…); the bottom one is an Earthly Branch (twelve: Zi, Chou, Yin…). Each belongs to one of the Five Elements.", "general rule of the Ziping method"),
    "十神": ("How each other character relates to the Day Master: produces it, is produced by it, controls it, is controlled by it, or is the same element, each split by polarity. Ten in all, used as metaphors for people and affairs.", "general rule of the Ziping method ⚖ meanings are the common reading"),
    "藏干": ("Stems hidden inside a branch. The main qi matters most, then the middle and residual qi.", "common hidden-stem table ⚖"),
    "通根": ("A stem finds the same element among the hidden stems of a branch, like a tree with roots. More roots, and main-qi roots, make it steadier.", "common Ziping reading ⚖"),
    "透干": ("A stem hidden in a branch also appears as a stem, so its strength shows openly.", "common Ziping reading ⚖"),
    "月令": ("The branch of your birth month. It decides which element is strongest in that season and is the most important factor in judging the Day Master's strength.", "general rule of the Ziping method"),
    "司令": ("Within a month, different stems take turns to rule. The " + _SM + " section on the ruling stems lists how many days each rules after the solar term.", "✅ " + _SM + ", vol. 2"),
    "旺相休囚死": ("How strong each element is in the season: in season it is Prosperous, then Strong, Resting, Trapped, and weakest Dead.", "✅ " + _SM + ", vol. 2"),
    "十二长生": ("The Day Master's state on each branch. Old books compare it to twelve stages of a life, from birth to the grave.", "✅ " + _SM + ", vol. 2; the book says strong stages are 'not necessarily good'"),
    "合": ("Two characters combine and hold on to each other. " + _SM + ": 'combination means harmony.' Combining into another element needs conditions; only the combination is marked here.", "✅ " + _SM + ", vol. 2"),
    "冲": ("Two opposite branches clash, which brings change. The book says a clash 'may be good or bad and cannot be judged in general': it depends on whether a helpful or harmful character is hit.", "✅ " + _SM + ", vol. 2"),
    "刑": ("Punishment. The book compares it to 'husband and wife who come together yet hurt each other': harm within closeness. Self-punishment is the same branch meeting itself.", "✅ " + _SM + ", vol. 2"),
    "害": ("Harm: the book calls these 'branches that encroach on each other'; they get in each other's way.", "✅ " + _SM + ", vol. 2"),
    "三合": ("Three branches complete a set and form one strong element (e.g. Shen, Zi and Chen form Water).", "✅ " + _SM + ", vol. 2"),
    "三会": ("The three branches of one direction are all present (e.g. Yin, Mao, Chen: the Wood of the east), concentrating that element.", "✅ Yuan Hai Zi Ping 渊海子平"),
    "三合缺一": ("Only two of a Three Harmony set are present. The book says 'with one of the three missing, the set does not form.' Watch for a Luck Pillar or year that brings the third.", "✅ " + _SM + ", vol. 2"),
    "空亡": ("In each ten-day cycle of the sixty, two branches are left out: they are 'void'. The book says Void 'should not be read as bad on that account'.", "✅ " + _SM + ", vol. 3"),
    "禄": ("The home position of the day stem. The book: 'Lu is rank and salary, to be enjoyed when in power.'", "✅ " + _SM + ", vol. 3"),
    "羊刃": ("One step beyond Prosperity: too strong, with its edge too exposed. The book: 'when Lu goes too far, the blade appears.'", "✅ " + _SM + ", vol. 3"),
    "天乙贵人": ("The most honoured auspicious star in the old books: 'wherever it goes, all malign stars quietly withdraw.' Popularly, help from benefactors.", "✅ " + _SM + ", vol. 3"),
    "驿马": ("Movement, relocation and change. The book calls it 'a spirit of happy events'.", "✅ " + _SM + ", vol. 3"),
    "咸池": ("Popularly 'Peach Blossom': charm and romantic attraction. The book's comments are negative; this skill does not repeat them or judge character from it.", "✅ " + _SM + ", vol. 2"),
    "纳音": ("The traditional image element of each of the sixty pairs (e.g. Roadside Earth, Fire below the Mountain).", "✅ " + _SM + ", vol. 1"),
    "起运": ("The age, in years and months, at which the first Luck Pillar starts, counted from birth to the next (or previous) solar term.", "general rule of the Ziping method"),
    "大运": ("The background that changes every ten years, like the seasons of a life.", "general rule of the Ziping method"),
    "流年": ("The stem and branch of each year, like that year's weather; read it together with the chart and the Luck Pillar.", "general rule of the Ziping method"),
    "调候": ("Which element the chart needs to balance the warmth, cold, dryness or damp of the birth season. The Qiong Tong Bao Jian 穷通宝鉴 is devoted to this.", "✅ Qiong Tong Bao Jian 穷通宝鉴"),
    "用神": ("The element that helps this chart most. This is a judgement; schools may choose differently, so look at the reasons.", "⚖ a judgement"),
    "喜神": ("An element that helps the chart and supports the Useful God.", "⚖ a judgement"),
    "忌神": ("An element that works against the chart.", "⚖ a judgement"),
    "五行个数": ("How many of the eight characters belong to each element. It is only a count: not strength, and not 'add whatever is missing'.", "note by this project"),
}


def page_data(lang: str = "zh") -> dict:
    if lang == "en":
        from . import terms_en
        return {"gan_xiang": GAN_XIANG, "gan_xiang_en": GAN_XIANG_EN, "shishen": SHISHEN_EN,
                "changsheng": {k: (terms_en.CHANGSHENG[k][1], q, CHANGSHENG_QUOTE_EN[k]) for k, (_, q) in CHANGSHENG.items()},
                "wangxiang": WANGXIANG_EN, "terms": TERMS_EN}
    return {"gan_xiang": GAN_XIANG, "shishen": SHISHEN, "changsheng": CHANGSHENG,
            "wangxiang": WANGXIANG, "terms": TERMS}


def markdown() -> str:
    """生成 bazi-mingli 的 references/glossary.md。"""
    out = ["# 八字术语白话释义", "",
           "> 由计算包的 glossary.py 生成，交互命盘里的术语解释与此一致。不要手改本文件。",
           "> 回答用户时，术语第一次出现就用这里的白话解释一句。✅ = 原文已核对，⚖ = 通行释义或判断。", "",
           "## 常用术语", "", "| 术语 | 白话 | 出处 / 口径 |", "|------|------|------|"]
    out += [f"| {k} | {v[0]} | {v[1]} |" for k, v in TERMS.items()]
    out += ["", "## 十神", "", "⚖ 子平通行释义；关系由生克与阴阳推出。", "",
            "| 十神 | 一词 | 与日主的关系 | 通行释义 |", "|------|------|------|------|"]
    out += [f"| {k} | {a} | {b} | {c} |" for k, (a, b, c) in SHISHEN.items()]
    out += ["", "## 十二长生", "", f"✅ {SANMING}卷二引《三命提要》。", "",
            "| 阶段 | 白话 | 原文 |", "|------|------|------|"]
    out += [f"| {k} | {a} | 「{b}」 |" for k, (a, b) in CHANGSHENG.items()]
    out += ["", "## 旺相休囚死", "", f"✅ {SANMING}卷二：春木、夏火、六月土、秋金、冬水当令。", "",
            "| 状态 | 白话 |", "|------|------|"]
    out += [f"| {k} | {v} |" for k, v in WANGXIANG.items()]
    out += ["", "## 天干物象", "", f"✅ {SANMING}卷二「论天干阴阳生死」。可用来向用户形容日主，如「丁火：在天为列星，在地为灯火」。", "",
            "| 天干 | 原文 |", "|------|------|"]
    out += [f"| {k} | 「{v}」 |" for k, v in GAN_XIANG.items()]
    return "\n".join(out) + "\n"
