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


def analyse(metrics, method):
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
    explanations = {
        "水": "水面在这一单元的土地覆盖信号中突出，以水为主；按真实覆盖统计取象，不由附近某个景点外推。",
        "木": "乔木、灌丛、草地等植被共同构成主要生长景观，以木为主；这是现代植被取象，不等同于传统直形木体。",
        "土": "以建成地、耕地或裸地等承载空间为主要底层信号，暂以土为主；这是公开的现代底层归类，不是判定这里必然属于传统方形土体。",
        "金": "功能资料中的商业、工业用地或许可分区在本单元形成显著功能信号，以金为主；不是看到一座银行就给整个地区定性。",
        "火": "功能资料中的零售服务分区或演艺线索形成较强展示、传播与消费活动信号，以火为主；不把这个信号当作气温、火灾风险或实测能量。",
    }
    gap = signals[primary] - signals[ranking[1]]
    confidence = "中" if metrics["sample_count"] >= 100 and gap >= .2 else "低"
    basis = metrics.get("function_basis", "OSM用地及设施")
    if method == "function" and "规划" in basis and primary in ("金", "火"):
        confidence = "低"
    if metrics["sampling"] != "50m多数分类统计":
        confidence = "低"
    return {
        "primary": primary,
        "secondary": secondary,
        "confidence": confidence,
        "confidence_reason": ("规划资料只表示许可用途，不等于当前营业用途。" if "规划" in basis else "") + "仅表示本规则下的证据区分度；2021年土地覆盖与功能资料的时效性/完整性限制现状判断，尚未经实地校验。"
                             + ("本单元较小，采用代表点补样，置信度降低。" if metrics["sampling"] != "50m多数分类统计" else ""),
        "reason": explanations[primary] + ("兼象反映同时存在的" + "、".join(secondary) + "信号，不是五行百分比。" if secondary else ""),
        "facts": [
            f"单元面积约 {metrics['area_km2']:.3f} km²；土地覆盖以2021年WorldCover分类在50m汇总网格上的有效样本统计。",
            f"水面约 {water:.1%}，植被约 {vegetation:.1%}，建成地约 {built:.1%}，耕地/裸地等约 {open_land:.1%}。这些是土地覆盖比例，不是五行能量占比。",
            f"{basis}：商业/工业分区信号覆盖约 {metrics['commercial_industrial']:.1%}，零售分区约 {metrics['retail']:.1%}，已研究演艺区范围约 {metrics.get('culture_area',0):.1%}，演艺/影院等对象 {metrics['culture_count']} 项（可能重复或遗漏）；未收录不等于实际不存在。",
        ],
        "limitations": "格网是连续统计单元，不是天然风水界线；边缘与混合用地会随分析尺度改变。"
                       "土可作为有覆盖数据但缺少更强功能信号时的底层归类，相关结论不冒充古法定论；"
                       "不以分类结果推断住宅财运或个人运势。",
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


def relative_analyses(metrics_list, scope_name):
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
        lead = (f"本单元的{WHAT[primary]}信号高于{scope_name}约 {p:.0%} 的单元，是这里相对最突出的一行"
                if p > 0 else f"本单元各行信号都很弱，暂以绝对信号最大的{primary}为主")
        reason = (XING[primary] + lead + f"；这是与本范围其他地方比较的结果，不表示{WHAT[primary]}在本单元占多数（约 {share:.0%}）。"
                  + ("兼象为同样高于范围内多数单元的" + "、".join(secondary) + "。" if secondary else ""))
        table = "、".join(f"{e} {pct[e][i]:.0%}" if pct[e][i] else f"{e} 证据不足" for e in ELEMENTS)
        out.append({
            "primary": primary,
            "secondary": secondary,
            "confidence": confidence,
            "confidence_reason": f"主象百分位 {p:.1%}，比次高一行高 {max(gap, 0):.1%}；百分位至少80%且领先至少10%才标中。"
                                 + ("规划资料只表示许可用途。" if "规划" in basis else "")
                                 + "功能资料的完整性限制判断，尚未经实地校验。",
            "reason": reason,
            "facts": [f"在{scope_name}内的百分位（信号低于 {RELATIVE_FLOOR} 记为证据不足）：{table}。",
                      *analyse(metrics, "function")["facts"]],
            "limitations": "相对取象依赖所比较的范围：同一地方放进别的城市或范围，结果可能不同，不同城市之间不能直接比较。"
                           "百分位不是五行占比；格网不是天然风水界线，也不以分类推断住宅财运或个人运势。",
        })
    return out
