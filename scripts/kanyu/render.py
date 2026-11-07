"""文字输出。所有面向模型 / 用户的文本格式集中在此，计算模块不做格式化。"""

from __future__ import annotations

from .almanac import DayInfo
from .bazhai import YOUNIAN_NOTE, YOUNIAN_ORDER, MinGua, younian
from .bazi import Bazi
from .core import (GRID, LUOSHU_PATH, NUM_PALACE, PALACE_DIR, STAR_NAMES, WEEKDAYS, YUANLONG, ZHI,
                   deg_to_mountain, fly, mountain_yinyang, mountain_yuanlong, wuxing_of)
from .feixing import Chart, jian_warnings, palace_flags, star_status
from .zeri import ZeriResult
from .zibai import YearSha, monthly_center


def display_width(s: str) -> int:
    return sum(2 if ord(ch) > 0x2E80 else 1 for ch in s)


def grid(cell, width: int = 14) -> str:
    """cell(palace) -> list[str]；按上南下北布局输出九宫格。"""
    sep = "+" + ("-" * width + "+") * 3
    lines = [sep]
    for row in GRID:
        cells = [cell(p) for p in row]
        for i in range(max(len(c) for c in cells)):
            parts = []
            for c in cells:
                t = c[i] if i < len(c) else ""
                parts.append(" " + t + " " * max(width - display_width(t) - 1, 0))
            lines.append("|" + "|".join(parts) + "|")
        lines.append(sep)
    return "\n".join(lines)


def _statuses(yun: int) -> str:
    return "，".join(f"{n}={star_status(n, yun)}" for n in range(1, 10))


# --- 飞星 ------------------------------------------------------------------------

def feixing(ch: Chart, *, annual: int | None = None, month: int | None = None,
            facing_deg: float | None = None, yun_note: str = "",
            current_yun: int | None = None) -> str:
    yun, sit, facing = ch.yun, ch.sit, ch.facing
    out = [f"【{yun}运 · {sit}山{facing}向】{'（替卦）' if ch.tigua else '（下卦）'}"]
    if yun_note:
        out.append(yun_note)
    out.append(f"坐 {sit}山：{ch.sit_palace}宫 {PALACE_DIR[ch.sit_palace]}，"
               f"{YUANLONG[mountain_yuanlong(sit)]}龙，玄空阴阳 {mountain_yinyang(sit)}")
    out.append(f"向 {facing}山：{ch.face_palace}宫 {PALACE_DIR[ch.face_palace]}")
    if facing_deg is not None:
        sit_deg = (facing_deg + 180) % 360
        _, off = deg_to_mountain(sit_deg)
        out.append(f"罗盘：坐 {sit_deg:.1f}° / 向 {facing_deg:.1f}°，偏离{sit}山中线 {off:+.1f}°")
        out.extend(jian_warnings(sit, off))
    for label, e in (("山星", ch.shan_entry), ("向星", ch.xiang_entry)):
        yy = mountain_yinyang(e.by)
        why = f"依{e.by}山（{yy}）" if e.n != 5 else f"五入中，依{e.by}山本身（{yy}）"
        line = f"{label}：运盘 {e.n} 入中，{why} → {'顺飞' if e.forward else '逆飞'}"
        if e.replaced:
            line += f"；替卦以 {e.center} 代 {e.n} 入中"
        out.append(line)

    ann = fly(annual) if annual else None
    mon = fly(month) if month else None

    def cell(p):
        tag = PALACE_DIR[p]
        if p == ch.sit_palace:
            tag += "(坐)"
        if p == ch.face_palace:
            tag += "(向)"
        rows = [f"{p} {tag}", f"山{ch.shan[p]} 向{ch.xiang[p]}", f"运{ch.yunpan[p]}"]
        extra = ([f"年{ann[p]}"] if ann else []) + ([f"月{mon[p]}"] if mon else [])
        if extra:
            rows.append(" ".join(extra))
        return rows

    out += ["", "九宫（上南下北；山=山星管人丁，向=向星管财，运=运星）：", grid(cell, 16), ""]
    out.append("格局：" + ("；".join(ch.patterns) if ch.patterns
                          else "无特殊格局（非旺山旺向/上山下水/双星）"))
    out += ["", f"{yun}运星曜旺衰：" + _statuses(yun)]
    if current_yun is not None and current_yun != yun:
        out.append(f"（注：本盘为{yun}运盘；当前为{current_yun}运，论现时旺衰亦可参考"
                   f"{current_yun}运：" + _statuses(current_yun) + "）")

    out += ["", "各宫星组合："]
    for p in LUOSHU_PATH:
        s, x = ch.shan[p], ch.xiang[p]
        line = (f"  {p}({PALACE_DIR[p]})：山{s}{STAR_NAMES[s][2:]} 向{x}{STAR_NAMES[x][2:]} "
                f"运{ch.yunpan[p]}")
        if ann:
            line += f" 年{ann[p]}"
        flags = palace_flags(s, x, ann[p] if ann else None)
        if flags:
            line += "  ⚠ " + "、".join(flags)
        out.append(line)
    if annual:
        out.append(f"\n流年中宫 {annual}（{STAR_NAMES[annual]}）"
                   + (f"，流月中宫 {month}" if month else ""))
    return "\n".join(out)


# --- 八宅 ------------------------------------------------------------------------

def younian_table(gua: str, title: str) -> list[str]:
    t = younian(gua)
    return [title] + [f"  {k}：{PALACE_DIR[t[k]]}（{t[k]}）  {YOUNIAN_NOTE[k]}" for k in YOUNIAN_ORDER]


def person(birth: str, mg: MinGua, note: str) -> list[str]:
    jg = f"（{mg.jigong}）" if mg.jigong else ""
    return [f"出生 {birth}，{'男' if mg.gender == 'm' else '女'}命，按立春计年 {mg.year}{note}",
            f"命卦：{mg.number} → {mg.gua}卦{jg}，{mg.group}命"]


def house(sit: str, facing: str, gua: str, group: str) -> list[str]:
    return [f"宅：坐{sit}向{facing} → 坐{PALACE_DIR[gua]}，{gua}宅（{group}宅）"]


def match(house_group: str, person_group: str) -> str:
    same = house_group == person_group
    return (f"宅命配合：{house_group}宅 × {person_group}命 → "
            + ("相配" if same else "不配（可以个人吉方安排床位、书桌朝向作调整）"))


# --- 流年 ------------------------------------------------------------------------

def year_line(s: YearSha) -> str:
    return (f"【{s.year} {s.ganzhi}年】中宫 {STAR_NAMES[s.center]}；五黄 {s.wuhuang}，二黑 {s.erhei}；"
            f"太岁 {s.taisui}，岁破 {s.suipo}，三煞 {s.sansha}")


def year_detail(s: YearSha) -> str:
    ann = fly(s.center)
    return "\n".join([
        grid(lambda p: [f"{p} {PALACE_DIR[p]}", f"{STAR_NAMES[ann[p]]}"], 14),
        "流月中宫（寅月起）：" + " ".join(
            f"{ZHI[(i + 1) % 12]}月{monthly_center(s.year, i)}" for i in range(1, 13)),
    ])


# --- 历法 / 择日 ------------------------------------------------------------------

def _join(xs: list[str]) -> str:
    return "、".join(xs) or "—"


def day(info: DayInfo, ys: YearSha) -> str:
    d = info.date
    out = [f"【{d:%Y-%m-%d} 周{WEEKDAYS[d.weekday()]}】农历{info.lunar}",
           f"四柱：{info.year_gz}年 {info.month_gz}月 {info.day_gz}日 {info.time_gz}时（时柱按 {d:%H:%M}）",
           f"节气：{info.jieqi}（月建 {info.month_zhi}）",
           f"建除：{info.jianchu}日    值神：{info.tianshen}",
           info.chong,
           f"吉神：{_join(info.jishen)}",
           f"凶煞：{_join(info.xiongsha)}",
           f"宜：{_join(info.yi)}",
           f"忌：{_join(info.ji)}"]
    if info.flags:
        out.append(f"⚠ 大忌：{'、'.join(info.flags)}")
    if info.suji:
        out.append(f"△ 通书俗忌：{'、'.join(info.suji)}（无《协纪辨方书》出处，仅供参考）")
    out.append(f"年家：太岁{ys.taisui}，岁破{ys.suipo}，三煞{ys.sansha}，流年五黄{ys.wuhuang}")
    return "\n".join(out)


def zeri(r: ZeriResult, top: int = 8) -> str:
    out = [f"【择日 · {r.event}】{r.start} 至 {r.end}"]
    if r.persons:
        out.append("当事人：" + "，".join(p.label for p in r.persons))
    for s in r.years:
        out.append(f"{s.year}年{s.ganzhi}：太岁{s.taisui}，岁破{s.suipo}，三煞{s.sansha}，"
                   f"流年五黄{s.wuhuang}、二黑{s.erhei}")
    out += ["", f"候选吉日（按分数排序，共 {len(r.good)} 天合格，列前 {min(top, len(r.good))}）："]
    for ds in r.good[:top]:
        i, d0 = ds.info, ds.info.date.date()
        out.append(f"  {d0} 周{WEEKDAYS[d0.weekday()]} {i.day_gz}日 "
                   f"农历{i.lunar_md}  分{ds.score}：{'，'.join(ds.reasons)}")
        out.append(f"      {i.chong}；凶煞：{_join(i.xiongsha[:6])}")
        if ds.notes:
            out.append(f"      △ {'、'.join(ds.notes)}")
    if not r.good:
        out.append("  （范围内无合格日，建议放宽日期范围）")
    out += ["", f"已排除 {len(r.bad)} 天，例如："]
    for ds in r.bad[:10]:
        i = ds.info
        out.append(f"  {i.date.date()} {i.day_gz}日 {i.jianchu}日：{'、'.join(ds.excluded)}")
    out += ["", "说明：评分为筛选辅助（宜忌出自通书体系的黄历数据 + 建除 + 黄道 + 德神），"
                "月破/正四废/冲当事人/黄历明忌为硬性排除；岁破日、受死为通书俗忌，仅标注（△）不排除。"
                "出处见 references/sources.md。时辰与方位需另行配合。"]
    return "\n".join(out)


# --- 八字 ------------------------------------------------------------------------

def bazi(b: Bazi) -> str:
    out = []
    if b.solar_delta is not None:
        out.append(f"真太阳时：{b.input_time:%Y-%m-%d %H:%M} → {b.birth:%Y-%m-%d %H:%M}"
                   f"（经度 {b.longitude}°，修正 {b.solar_delta:+.1f} 分钟）")
    out.append(f"出生：{b.birth:%Y-%m-%d %H:%M}（农历{b.lunar}）")
    out.append("四柱：" + "  ".join(f"{n}{p}" for n, p in zip("年月日时", b.pillars)))
    out.append(f"日主：{b.day_gan}（{wuxing_of(b.day_gan)}）  月令：{b.month_zhi}")
    out.append("十神（天干）：" + "  ".join(b.shishen_gan))
    out.append("藏干：" + "  ".join(f"{p[1]}[{''.join(h)}]" for p, h in zip(b.pillars, b.hide_gan)))
    out.append("纳音：" + "  ".join(b.nayin))
    out.append("五行（八字表面计数，未计藏干与旺衰）：" + " ".join(f"{k}{v}" for k, v in b.wuxing_count.items()))
    out.append(f"起运：出生后 {b.qiyun[0]}年{b.qiyun[1]}月{b.qiyun[2]}天")
    out.append("大运：" + "  ".join(f"{dy.ganzhi}({dy.start_year})" for dy in b.dayun))
    mg = b.mingua
    out.append(f"命卦（八宅）：{mg.number} {NUM_PALACE[mg.number]}卦，{mg.group}命")
    out.append("注：日主强弱、格局、用神属于判断，需结合月令、通根、透干综合论断，本工具不代为判定。")
    return "\n".join(out)
