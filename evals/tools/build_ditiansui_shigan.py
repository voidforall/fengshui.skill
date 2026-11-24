"""从维基文库《滴天髓阐微》原文（wikitext）抽取「通神论·七、天干」十干各条：原文、原注、任氏注，不含命例。

用法：python3 -I build_ditiansui_shigan.py <滴天髓闡微.wiki> <输出 shigan.md>
生成 skills/bazi-mingli/references/shigan.md，论命时按日干读对应一条（playbook 第三节第 2 步）。
"""
import re
import sys

GAN = "甲乙丙丁戊己庚辛壬癸"
GZ_LINE = re.compile(r"^[甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥]")


def clean(s):
    return re.sub(r"\{\{[^{}|]*\||\}\}|'''", "", s).strip()


def main(src, out):
    lines = [clean(l) for l in open(src, encoding="utf-8").read().splitlines()]
    start = lines.index("===七、天干===")
    end = next(i for i in range(start + 1, len(lines)) if lines[i].startswith("===八、"))
    body = [l for l in lines[start + 1:end] if l]
    entries, cur = [], None
    for l in body:
        if cur and l[0] == cur["verse"][0] and not cur["notes"] and not GZ_LINE.match(l):
            cur["notes"].append("原注：" + l)        # 己土条原注未标「原注」
        elif l[0] in GAN and not GZ_LINE.match(l) and not l.startswith(("原注", "任氏")):
            cur = {"verse": l, "notes": []}
            entries.append(cur)
        elif cur and l.startswith(("原注", "任氏")):
            cur["notes"].append(l)
    assert [e["verse"][0] for e in entries] == list(GAN), [e["verse"][:4] for e in entries]
    md = ["# 十干性情（《滴天髓阐微》通神论·天干）", "",
          "> 由仓库 evals/tools/build_ditiansui_shigan.py 从维基文库原文抽取，只录原文、原注与任铁樵注，不含命例。不要手改。",
          "> 论命时读日干那一条：看此干在本季的虚实、喜忌，再与通根、寒暖燥湿合看（playbook 第三节）。", ""]
    for e in entries:
        md += [f"## {e['verse'][0]}", "", f"**原文**：{e['verse']}", ""]
        md += [n.replace("原注：", "**原注**：", 1).replace("任氏曰：", "**任氏曰**：", 1).replace("任氏曰；", "**任氏曰**：", 1) + "\n"
               for n in e["notes"]]
    open(out, "w", encoding="utf-8").write("\n".join(md).rstrip() + "\n")
    print(out, sum(len(x) for x in md))


if __name__ == "__main__":
    main(*sys.argv[1:])
