"""bazi-mingli 的文字输出。计算模块不做格式化。"""

from __future__ import annotations

from .bazi import ZI_RULES, Bazi, dayun_forward
from .core import NUM_PALACE, wuxing_of


def _age(y: int, m: int) -> str:
    return f"{y}岁" + (f"{m}个月" if m else "")


def bazi_time(b: Bazi) -> list[str]:
    m = b.moment
    out = [f"出生时间：{m.clock:%Y-%m-%d}" + (f" {m.clock:%H:%M}" if m.time_known else "（时辰不详）")
           + f"（{m.tz}）  农历{b.lunar}"]
    if m.time_known:
        if m.dst_minutes:
            out.append(f"夏令时：出生时当地实行夏令时，钟表 {m.clock:%H:%M} 扣 {m.dst_minutes} 分钟 → 当地标准时 {m.standard:%H:%M}")
        if m.solar is not None:
            out.append(f"真太阳时：{m.solar:%Y-%m-%d %H:%M}（经度 {m.longitude}°，相对标准时修正 {m.solar_delta:+.1f} 分钟）")
        else:
            out.append("真太阳时：未给出生地经度，按当地标准时排时柱（时辰交界附近请补经度）")
        out.append(f"口径：年柱、月柱按北京时间 {m.beijing:%Y-%m-%d %H:%M} 比对立春与节气；"
                   f"日柱、时柱用{'真太阳时' if m.solar else '当地标准时'}；子时：{ZI_RULES[b.zi_rule]}")
    else:
        out.append("口径：只排年、月、日三柱；年柱、月柱按当日正午比对节气")
    out += [f"⚠ {w}" for w in b.warnings]
    return out


def bazi(b: Bazi) -> str:
    out = bazi_time(b)
    ps = b.pillars
    out.append("")
    out.append("四柱：" + "  ".join(f"{p.name}{p.ganzhi}" for p in ps))
    s = b.siling
    out.append(f"日主：{b.day_gan}（{'阳' if b.day_gan in '甲丙戊庚壬' else '阴'}{wuxing_of(b.day_gan)}）  "
               f"月令：{b.month_zhi}（{s['jie']}后第 {s['day_n']} 日，{s['ruler']}司令）")
    w = b.wangxiang
    out.append(f"旺相休囚死（《三命通会》）：生于{w['season']}，{w['wang']}当令；日主{wuxing_of(b.day_gan)}为「{w['day']}」。"
               + " ".join(f"{k}{v}" for k, v in w["states"].items()))
    out.append("十神（天干）：" + "  ".join(f"{p.name}{p.gan}{p.gan_shishen}" for p in ps))
    out.append("藏干（本气/中气/余气·十神）：")
    for p in ps:
        out.append(f"  {p.name}支{p.zhi}：" + "  ".join(f"{h.gan}（{h.qi}·{h.shishen}）" for h in p.hidden))
    out.append(f"十二长生（日干{b.day_gan}临各支）：" + "  ".join(f"{p.name}支{p.zhi}{p.changsheng}" for p in ps))
    out.append("纳音：" + "  ".join(f"{p.name}{p.nayin}" for p in ps))
    out.append(f"月令人元司事（《三命通会》）：{b.month_zhi}月 " + "、".join(f"{t['name']}{t['days']}日" for t in s["table"])
               + f"；交{s['jie']}于 {s['jie_time']:%Y-%m-%d %H:%M}（北京时间）")
    out.append("通根（天干在地支藏干中见同五行）：")
    for r in b.roots:
        roots = "、".join(f"{x['pillar']}支{x['zhi']}{x['qi']}{x['hidden']}" for x in r["roots"]) or "无"
        out.append(f"  {r['pillar']}干{r['gan']}：{roots}")
    tou = "；".join(f"{t['pillar']}支{t['zhi']}{t['qi']}{t['hidden']}透{'、'.join(x + '干' for x in t['at'])}" for t in b.tou)
    out.append(f"透干（藏干原样见于天干）：{tou or '无'}")
    rel = [r["label"] for r in b.relations["gan"] + b.relations["zhi"]]
    out.append("原局干支关系：" + ("；".join(rel) if rel else "无合冲刑害"))
    out.append("五行计数（只是个数，不代表旺衰）：天干地支 " + " ".join(f"{k}{v}" for k, v in b.wuxing_count.items())
               + "；藏干 " + " ".join(f"{k}{v}" for k, v in b.wuxing_hidden.items()))
    if b.shensha:
        out.append("神煞（《三命通会》查表，不单独论吉凶）：" + "；".join(
            f"{x['name']}：依{x['basis']}查得{x['targets']}，见于{'、'.join(x['hits'])}" for x in b.shensha))
    else:
        out.append("神煞（《三命通会》查表）：禄、羊刃、天乙贵人、驿马、咸池、空亡均未见于柱中")
    t = b.tiaohou
    out.append(f"调候原文（{t['book']}{t['section']}，{t['month']}{b.day_gan}{wuxing_of(b.day_gan)}；月令按节气）：")
    for q in t["passages"]:
        out.append(f"  [{q['kind']}·第{q['line']}行] {q['text']}")
    out.append("")
    out.append(f"起运：出生后 {b.qiyun[0]}年{b.qiyun[1]}月{b.qiyun[2]}天，{b.qiyun_date:%Y-%m-%d} 交运"
               f"（{'顺' if dayun_forward(ps[0].gan, b.gender) else '逆'}排）")
    out.append("大运（交运日期 · 周岁 · 干十神/支本气十神 · 日干长生 · 与原局关系）：")
    for dy in b.dayun:
        mark = " ◀" if dy.ganzhi == b.focus_dayun else ""
        rel = "；".join(dy.relations) or "—"
        out.append(f"  {dy.ganzhi}  {dy.start:%Y-%m}  {_age(*dy.start_age)}  {dy.gan_shishen}/{dy.zhi_shishen}  "
                   f"{dy.changsheng}  {rel}{mark}")
    f = b.focus
    if f:
        where = f"行{b.focus_dayun}大运" if b.focus_dayun else "起运前"
        out.append(f"流年 {f.year} {f.ganzhi}（{f.age}周岁，{where}）：干{f.gan_shishen}，日干临{f.ganzhi[1]}{f.changsheng}；"
                   + ("；".join(f.relations) or "与原局无合冲刑害"))
    mg = b.mingua
    out.append(f"命卦（八宅）：{mg.number} {NUM_PALACE[mg.number]}卦，{mg.group}命")
    out.append("注：以上为排盘与查表事实。日主强弱、格局、用神属于判断，须结合月令、通根、透干、调候综合论断，并说明所依流派；本工具不代为判定。")
    return "\n".join(out)


def pillars_chart(c) -> str:
    """只给四柱时的输出：查表事实、根气轻重、寒暖燥湿、调候原文、大运干支。"""
    ps = c.pillars
    out = ["只给四柱：以下为查表事实，不涉出生时刻（起运岁数、流年周岁、真太阳时需出生时间）。", ""]
    out.append("四柱：" + "  ".join(f"{p.name}{p.ganzhi}" for p in ps) + f"（{'乾造' if c.gender == 'm' else '坤造'}）")
    out.append(f"日主：{c.day_gan}（{'阳' if c.day_gan in '甲丙戊庚壬' else '阴'}{wuxing_of(c.day_gan)}）  月令：{c.month_zhi}")
    w = c.wangxiang
    out.append(f"旺相休囚死（《三命通会》）：生于{w['season']}，{w['wang']}当令；日主{wuxing_of(c.day_gan)}为「{w['day']}」。"
               + " ".join(f"{k}{v}" for k, v in w["states"].items()))
    out.append("十神（天干）：" + "  ".join(f"{p.name}{p.gan}{p.gan_shishen}" for p in ps))
    out.append("藏干（本气/中气/余气·十神）：")
    for p in ps:
        out.append(f"  {p.name}支{p.zhi}：" + "  ".join(f"{h.gan}（{h.qi}·{h.shishen}）" for h in p.hidden))
    out.append(f"十二长生（日干{c.day_gan}临各支）：" + "  ".join(f"{p.name}支{p.zhi}{p.changsheng}" for p in ps))
    out.append("纳音：" + "  ".join(f"{p.name}{p.nayin}" for p in ps))
    out.append("通根（重根＝长生、临官、帝旺或本气；轻根＝墓库、余气、中气。《滴天髓阐微》：「天干得一比肩，不如地支得一余气墓库」）：")
    for r in c.roots:
        roots = "、".join(f"{x['pillar']}支{x['zhi']}{x['qi']}{x['hidden']}（{x['weight']}）" for x in r["roots"]) or "无根"
        out.append(f"  {r['pillar']}干{r['gan']}：{roots}")
    tou = "；".join(f"{t['pillar']}支{t['zhi']}{t['qi']}{t['hidden']}透{'、'.join(x + '干' for x in t['at'])}" for t in c.tou)
    out.append(f"透干（藏干原样见于天干）：{tou or '无'}")
    rel = [r["label"] for r in c.relations["gan"] + c.relations["zhi"]]
    out.append("原局干支关系：" + ("；".join(rel) if rel else "无合冲刑害"))
    cl = c.climate
    out.append(f"寒暖燥湿（事实，供调候参考）：月令{cl['month']}，{cl['season']}；"
               f"火见于 {'、'.join(cl['fire']) or '无'}；水见于 {'、'.join(cl['water']) or '无'}；"
               f"湿土（辰丑）{'、'.join(cl['wet_earth']) or '无'}；燥土（未戌）{'、'.join(cl['dry_earth']) or '无'}")
    out.append("五行计数（只是个数，不代表旺衰）：天干地支 " + " ".join(f"{k}{v}" for k, v in c.wuxing_count.items())
               + "；藏干 " + " ".join(f"{k}{v}" for k, v in c.wuxing_hidden.items()))
    if c.shensha:
        out.append("神煞（《三命通会》查表，不单独论吉凶）：" + "；".join(
            f"{x['name']}：依{x['basis']}查得{x['targets']}，见于{'、'.join(x['hits'])}" for x in c.shensha))
    t = c.tiaohou
    out.append(f"调候原文（{t['book']}{t['section']}，{t['month']}{c.day_gan}{wuxing_of(c.day_gan)}；月令按节气）：")
    for q in t["passages"]:
        out.append(f"  [{q['kind']}·第{q['line']}行] {q['text']}")
    out.append("")
    out.append(f"大运（{'顺' if dayun_forward(ps[0].gan, c.gender) else '逆'}排，自月柱起；起运岁数需出生时刻 · 干十神/支本气十神 · 日干长生 · 与原局关系）：")
    for dy in c.dayun:
        rel = "；".join(dy["relations"]) or "无"
        out.append(f"  {dy['ganzhi']}  {dy['gan_shishen']}/{dy['zhi_shishen']}  {dy['changsheng']}  {rel}")
    return "\n".join(out)
