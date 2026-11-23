"""Transparent modern interpretation rules; input proportions describe geography, not qi."""
MODEL_VERSION = "landcover-function-v2"
ELEMENTS = "金木水火土"


def function_signals(metrics):
    """综合口径的决策信号（相对取象也用它排百分位）。"""
    return {
        "水": metrics["water"] * 1.2,
        "木": metrics["vegetation"] * 1.1,
        "土": (metrics["open"] + metrics["built"]) * .65,
        "金": min(1, metrics["commercial_industrial"]) * 2,
        "火": min(1, metrics["retail"]) * 2.4 + metrics.get("culture_area", 0) * .9 + min(.8, metrics["culture_count"] * .16),
    }


def analyse(metrics, method, lang="zh"):
    """Assign every unit a main and optional secondary element from recorded evidence.

    Scores are decision signals, never probabilities or measured five-element shares.
    Missing source measurements must be handled before calling this function.
    """
    water = metrics["water"]
    vegetation = metrics["vegetation"]
    open_land = metrics["open"]
    built = metrics["built"]
    if method == "function":
        signals = function_signals(metrics)
    elif method == "landscape":
        signals = {"水": water, "木": vegetation, "土": open_land + built}
    else:
        raise ValueError("method must be landscape or function")
    ranking = sorted(signals, key=lambda key: (-signals[key], ELEMENTS.index(key)))
    primary = ranking[0]
    secondary = [key for key in ranking[1:]
                 if signals[key] >= .15 and signals[key] >= signals[primary] * .2][:2]
    gap = signals[primary] - signals[ranking[1]]
    confidence = "中" if metrics["sample_count"] >= 100 and gap >= .2 else "低"
    basis = metrics.get("function_basis", "OSM用地及设施")
    if method == "function" and "规划" in basis and primary in ("金", "火"):
        confidence = "低"
    if metrics["sampling"] != "50m多数分类统计":
        confidence = "低"
    t = TEXT[lang]
    planned = "规划" in basis
    small = metrics["sampling"] != "50m多数分类统计"
    return {
        "primary": primary,
        "secondary": secondary,
        "confidence": confidence,
        "confidence_reason": (t["planned"] if planned else "") + t["evidence_only"] + (t["small"] if small else ""),
        "reason": t["explain"][primary] + (t["secondary"](secondary) if secondary else ""),
        "facts": t["facts"](metrics, basis),
        "limitations": t["limitations"],
    }


def _pct(x):
    return f"{x:.1%}"


def _names(elements, lang):
    return "、".join(elements) if lang == "zh" else ", ".join(ELEMENT_EN[e] for e in elements)


ELEMENT_EN = {"金": "Metal", "木": "Wood", "水": "Water", "火": "Fire", "土": "Earth"}
# 功能资料口径（manifest 的 function_basis）的英文
BASIS_EN = {
    "OSM用地及设施": "OSM land use and amenities",
    "规划许可用途（非现状）＋演艺区资料": "zoning (permitted use, not current use) and performing-arts district data",
    "OSM用地及设施（国内用地标注覆盖不均）": "OSM land use and amenities (land-use tagging in China is uneven)",
}

# 单元说明文字。zh 与 en 逐条对应，判定规则只有一份（上面的代码）。
TEXT = {
    "zh": {
        "explain": {
            "水": "水面在这一单元的土地覆盖信号中突出，以水为主；按真实覆盖统计取象，不由附近某个景点外推。",
            "木": "乔木、灌丛、草地等植被共同构成主要生长景观，以木为主；这是现代植被取象，不等同于传统直形木体。",
            "土": "以建成地、耕地或裸地等承载空间为主要底层信号，暂以土为主；这是公开的现代底层归类，不是判定这里必然属于传统方形土体。",
            "金": "功能资料中的商业、工业用地或许可分区在本单元形成显著功能信号，以金为主；不是看到一座银行就给整个地区定性。",
            "火": "功能资料中的零售服务分区或演艺线索形成较强展示、传播与消费活动信号，以火为主；不把这个信号当作气温、火灾风险或实测能量。",
        },
        "secondary": lambda sec: "兼象反映同时存在的" + "、".join(sec) + "信号，不是五行百分比。",
        "planned": "规划资料只表示许可用途，不等于当前营业用途。",
        "evidence_only": "仅表示本规则下的证据区分度；2021年土地覆盖与功能资料的时效性/完整性限制现状判断，尚未经实地校验。",
        "small": "本单元较小，采用代表点补样，置信度降低。",
        "facts": lambda m, basis: [
            f"单元面积约 {m['area_km2']:.3f} km²；土地覆盖以2021年WorldCover分类在50m汇总网格上的有效样本统计。",
            f"水面约 {_pct(m['water'])}，植被约 {_pct(m['vegetation'])}，建成地约 {_pct(m['built'])}，耕地/裸地等约 {_pct(m['open'])}。这些是土地覆盖比例，不是五行能量占比。",
            f"{basis}：商业/工业分区信号覆盖约 {_pct(m['commercial_industrial'])}，零售分区约 {_pct(m['retail'])}，已研究演艺区范围约 {_pct(m.get('culture_area', 0))}，演艺/影院等对象 {m['culture_count']} 项（可能重复或遗漏）；未收录不等于实际不存在。",
        ],
        "limitations": "格网是连续统计单元，不是天然风水界线；边缘与混合用地会随分析尺度改变。"
                       "土可作为有覆盖数据但缺少更强功能信号时的底层归类，相关结论不冒充古法定论；"
                       "不以分类结果推断住宅财运或个人运势。",
    },
    "en": {
        "explain": {
            "水": "Water surface stands out in this cell's land-cover signal, so Water is the main element; this is read from actual cover statistics, not extrapolated from a nearby landmark.",
            "木": "Trees, shrubs and grassland together form the main growing landscape, so Wood is the main element; this is a modern vegetation reading, not the traditional upright Wood form.",
            "土": "Built-up land, farmland or bare ground is the main underlying signal, so Earth is the main element for now; this is a published modern base class, not a claim that the place has the traditional square Earth form.",
            "金": "Commercial or industrial land use or zoning in the function data forms a clear signal in this cell, so Metal is the main element; one bank does not decide the character of a whole district.",
            "火": "Retail and service zoning or performing-arts evidence in the function data forms a strong signal of display, exchange and consumption, so Fire is the main element; this signal is not temperature, fire risk or measured energy.",
        },
        "secondary": lambda sec: " The secondary element (" + ", ".join(ELEMENT_EN[e] for e in sec) + ") reflects signals that are also present; these are not five-element percentages.",
        "planned": "Zoning only shows permitted use, not current business use. ",
        "evidence_only": "This only shows how clearly the evidence separates under this rule; the 2021 land cover and the age and completeness of the function data limit what it says about today, and it has not been checked on the ground.",
        "small": " This is a small edge cell sampled at a representative point, so confidence is lower.",
        "facts": lambda m, basis: [
            f"Cell area about {m['area_km2']:.3f} km²; land cover counted from valid samples of the 2021 WorldCover classes on a 50 m grid.",
            f"Water about {_pct(m['water'])}, vegetation about {_pct(m['vegetation'])}, built-up about {_pct(m['built'])}, farmland or bare ground about {_pct(m['open'])}. These are land-cover shares, not shares of five-element energy.",
            f"{BASIS_EN.get(basis, basis)}: commercial/industrial signal covers about {_pct(m['commercial_industrial'])}, retail about {_pct(m['retail'])}, studied performing-arts district about {_pct(m.get('culture_area', 0))}; {m['culture_count']} performing-arts or cinema objects (may be duplicated or missed). Not recorded does not mean absent.",
        ],
        "limitations": "The grid is a continuous statistical unit, not a natural feng shui boundary; edges and mixed land use change with the scale of analysis. "
                       "Earth serves as the base class where there is cover data but no stronger function signal; this does not pose as an established classical rule, "
                       "and the result says nothing about the wealth of any home or the fortune of any person.",
    },
}


# --- 相对取象 ---------------------------------------------------------------------------
# 典籍依据（维基文库原文已核对）：
#   《尚书·洪范》：「水曰润下，火曰炎上，木曰曲直，金曰从革，土爰稼穑。」
#   《五行大义》卷一「辨体性」：「体者，以形质为名；性者，以功用为义。」
#     土「总于四行」「土苞四德，故其体能兼虚实」——土为承载四行的底色。
# 据此：土是底色，看每个单元在土之上相对全城最突出的是哪一行。百分位只在声明范围内比较。

RELATIVE_FLOOR = .05   # 信号低于此值视为证据不足，不参与相对取象
CLASSICS = [
    {"title": "《尚书·洪范》五行（维基文库）", "url": "https://zh.wikisource.org/wiki/尚書/洪範"},
    {"title": "《五行大义》卷一「辨体性」（维基文库）", "url": "https://zh.wikisource.org/wiki/五行大義/1"},
]
XING = {
    "水": "《洪范》「水曰润下」，《五行大义》释为「水流湿，就污下也」。",
    "木": "《洪范》「木曰曲直」，《五行大义》「木以温柔为体，曲直为性」，取其生长。",
    "火": "《洪范》「火曰炎上」，《五行大义》「火以明热为体」；以零售、演艺等聚人显扬的活动类比炎上，是现代类比。",
    "金": "《洪范》「金曰从革」，《五行大义》释为「从范而更，形革成器」「工冶铸作」；以工业制作类比从革，商贸归此是现代类比。",
    "土": "《五行大义》：土「总于四行」，「土苞四德，故其体能兼虚实」；建成与耕作承载之地取土为底色。",
}
WHAT = {"水": "水面", "木": "植被", "土": "建成与开放承载空间", "金": "商业、工业用地", "火": "零售、演艺功能"}
# 英文：原文附我们的译文（our translation）
XING_EN = {
    "水": "Hong Fan 洪范: 「水曰润下」 'water moistens and descends'; Wu Xing Da Yi 五行大义: 「水流湿，就污下也」 'water flows to the damp and seeks low ground' (our translation). ",
    "木": "Hong Fan 洪范: 「木曰曲直」 'wood bends and straightens'; Wu Xing Da Yi 五行大义: 「木以温柔为体，曲直为性」 'wood takes gentleness as its body and bending and straightening as its nature' (our translation), read here as growth. ",
    "火": "Hong Fan 洪范: 「火曰炎上」 'fire blazes upward'; Wu Xing Da Yi 五行大义: 「火以明热为体」 'fire takes brightness and heat as its body' (our translation). Reading retail and performing arts, which gather people and put things on show, as blazing upward is a modern analogy. ",
    "金": "Hong Fan 洪范: 「金曰从革」 'metal yields and is reshaped'; Wu Xing Da Yi 五行大义: 「从范而更，形革成器」 'it follows the mould and changes, its form reshaped into vessels' and 「工冶铸作」 'smelting and casting' (our translation). Reading industry as reshaping is an analogy; putting commerce here is a modern analogy. ",
    "土": "Wu Xing Da Yi 五行大义: Earth 「总于四行」 'unites the other four' and 「土苞四德，故其体能兼虚实」 'Earth embraces the four virtues, so its body holds both the empty and the solid' (our translation); land that carries building and farming is taken as the Earth base. ",
}
WHAT_EN = {"水": "water surface", "木": "vegetation", "土": "built and open supporting land",
           "金": "commercial and industrial land", "火": "retail and performing-arts function"}


def _percentiles(values):
    """平均秩百分位（0–1]：与范围内全部单元比较。"""
    ordered = sorted(values)
    n = len(values)
    out = []
    for v in values:
        lo = _bisect_left(ordered, v)
        hi = _bisect_right(ordered, v)
        out.append((lo + (hi - lo + 1) / 2) / n)
    return out


def _bisect_left(a, x):
    lo, hi = 0, len(a)
    while lo < hi:
        mid = (lo + hi) // 2
        if a[mid] < x:
            lo = mid + 1
        else:
            hi = mid
    return lo


def _bisect_right(a, x):
    lo, hi = 0, len(a)
    while lo < hi:
        mid = (lo + hi) // 2
        if x < a[mid]:
            hi = mid
        else:
            lo = mid + 1
    return lo


def relative_analyses(metrics_list, scope_name, lang="zh"):
    """相对取象：每行信号换算成在声明范围内的百分位，取百分位最高且达到证据门槛的一行。

    结果比绝对比较更均衡，因为它回答的是「这里比本城一般地方更突出的是什么」，
    不是「这里哪一行占多数」。不同城市、不同范围之间的结果不能直接比较。
    """
    signals = [function_signals(m) for m in metrics_list]
    pct = {}
    for e in ELEMENTS:
        values = [s[e] for s in signals]
        ranks = _percentiles(values)
        pct[e] = [r if v >= RELATIVE_FLOOR else 0.0 for r, v in zip(ranks, values)]
    out = []
    for i, metrics in enumerate(metrics_list):
        sig = signals[i]
        ranking = sorted(ELEMENTS, key=lambda e: (-pct[e][i], -sig[e], ELEMENTS.index(e)))
        primary = ranking[0]
        if pct[primary][i] == 0:   # 所有信号都低于门槛：以绝对信号最大者为主，低置信
            primary = max(ELEMENTS, key=lambda e: (sig[e], -ELEMENTS.index(e)))
        p = pct[primary][i]
        secondary = [e for e in ranking if e != primary and pct[e][i] >= .75][:2]
        others = [pct[e][i] for e in ELEMENTS if e != primary]
        gap = round(p - max(others), 6)   # 避免 0.0999… 这类浮点误差影响门槛
        basis = metrics.get("function_basis", "OSM用地及设施")
        confidence = "中" if round(p, 6) >= .8 and gap >= .1 and metrics["sampling"] == "50m多数分类统计" else "低"
        if "规划" in basis and primary in ("金", "火"):
            confidence = "低"
        share = {"水": metrics["water"], "木": metrics["vegetation"], "土": metrics["built"] + metrics["open"],
                 "金": metrics["commercial_industrial"], "火": metrics["retail"]}[primary]
        cells = [(e, pct[e][i]) for e in ELEMENTS]
        facts = analyse(metrics, "function", lang)["facts"]
        planned = "规划" in basis
        if lang == "en":
            what = WHAT_EN[primary]
            lead = (f"This cell's {what} signal is higher than about {p:.0%} of cells in {scope_name}, the element that stands out most here"
                    if p > 0 else f"All signals in this cell are weak; the element with the largest absolute signal, {ELEMENT_EN[primary]}, is used for now")
            reason = (XING_EN[primary] + lead
                      + f". This compares the cell with the rest of the area and does not mean {what} makes up most of the cell (about {share:.0%})."
                      + (" Secondary: " + ", ".join(ELEMENT_EN[e] for e in secondary) + ", also higher than most cells in the area." if secondary else ""))
            table = ", ".join(f"{ELEMENT_EN[e]} {v:.0%}" if v else f"{ELEMENT_EN[e]} insufficient evidence" for e, v in cells)
            out.append({
                "primary": primary, "secondary": secondary, "confidence": confidence,
                "confidence_reason": f"Main element percentile {p:.1%}, {max(gap, 0):.1%} ahead of the next; Medium requires at least 80% and a lead of at least 10%. "
                                     + ("Zoning only shows permitted use. " if planned else "")
                                     + "The completeness of the function data limits this judgement; it has not been checked on the ground.",
                "reason": reason,
                "facts": [f"Percentile within {scope_name} (signals below {RELATIVE_FLOOR} count as insufficient evidence): {table}.", *facts],
                "limitations": "The relative reading depends on the area compared: the same place inside another city or area may come out differently, so cities cannot be compared directly. "
                               "Percentiles are not five-element shares; the grid is not a natural feng shui boundary, and the result says nothing about the wealth of any home or the fortune of any person.",
            })
            continue
        lead = (f"本单元的{WHAT[primary]}信号高于{scope_name}约 {p:.0%} 的单元，是这里相对最突出的一行"
                if p > 0 else f"本单元各行信号都很弱，暂以绝对信号最大的{primary}为主")
        reason = (XING[primary] + lead + f"；这是与本范围其他地方比较的结果，不表示{WHAT[primary]}在本单元占多数（约 {share:.0%}）。"
                  + ("兼象为同样高于范围内多数单元的" + "、".join(secondary) + "。" if secondary else ""))
        table = "、".join(f"{e} {v:.0%}" if v else f"{e} 证据不足" for e, v in cells)
        out.append({
            "primary": primary,
            "secondary": secondary,
            "confidence": confidence,
            "confidence_reason": f"主象百分位 {p:.1%}，比次高一行高 {max(gap, 0):.1%}；百分位至少80%且领先至少10%才标中。"
                                 + ("规划资料只表示许可用途。" if planned else "")
                                 + "功能资料的完整性限制判断，尚未经实地校验。",
            "reason": reason,
            "facts": [f"在{scope_name}内的百分位（信号低于 {RELATIVE_FLOOR} 记为证据不足）：{table}。", *facts],
            "limitations": "相对取象依赖所比较的范围：同一地方放进别的城市或范围，结果可能不同，不同城市之间不能直接比较。"
                           "百分位不是五行占比；格网不是天然风水界线，也不以分类推断住宅财运或个人运势。",
        })
    return out
