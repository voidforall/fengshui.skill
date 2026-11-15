"""Transparent modern interpretation rules; input proportions describe geography, not qi."""
MODEL_VERSION = "landcover-function-v1"
ELEMENTS = "金木水火土"


def analyse(metrics, method):
    """Assign every unit a main and optional secondary element from recorded evidence.

    Scores are decision signals, never probabilities or measured five-element shares.
    Missing source measurements must be handled before calling this function.
    """
    water = metrics["water"]
    vegetation = metrics["vegetation"]
    open_land = metrics["open"]
    built = metrics["built"]
    signals = {"水": water, "木": vegetation, "土": open_land + built}
    if method == "function":
        signals = {
            "水": water * 1.2,
            "木": vegetation * 1.1,
            "土": (open_land + built) * .65,
            "金": min(1, metrics["commercial_industrial"]) * 2,
            "火": min(1, metrics["retail"]) * 2.4 + metrics.get("culture_area", 0) * .9 + min(.8, metrics["culture_count"] * .16),
        }
    elif method != "landscape":
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
