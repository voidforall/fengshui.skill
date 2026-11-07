"""由下载的古籍原文生成 evals/cases.json（引文程序化截取，避免手抄出错）。

用法：python3 -I build_cases.py <原文目录的上级> <输出 cases.json>
需要的原文（用 fetch_wikisource.py 下载到 <上级>/src/）：滴天髓闡微、窮通寶鑑、神峯通考，
以及《古今图书集成·艺术典》第680卷（以 action=render 取得，存为 src/gj680.txt）；
《滴天髓阐微》命例先用 extract_ditiansui.py 抽成 <上级>/dts.json。
"""
import json, re, sys
S = sys.argv[1]; OUT = sys.argv[2]
src = f"{S}/src"
dts = {c["id"]: c for c in json.load(open(f"{S}/dts.json", encoding="utf-8"))["cases"]}
qt = open(f"{src}/窮通寶鑑.wiki", encoding="utf-8").read()
sf = open(f"{src}/神峯通考.wiki", encoding="utf-8").read()
gjt = open(f"{src}/gj680.txt", encoding="utf-8").read()
WS = "https://zh.wikisource.org/wiki/"
GZ = r"[甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥]"
BAZI_Q = "{who}四柱：{p}。请判断日主旺衰与用神（喜用何五行），并简要说明理由。"
cases = []

def norm(s): return re.sub(r"\s+", "", s.replace("'''", ""))

def bazi_case(cid, who, focus, keys):
    c = dts[cid]
    cases.append({"id": cid, "category": "八字",
        "source": {"book": "任铁樵《滴天髓阐微》", "location": f"{c['section']}（维基文库原文第 {c['line']} 行）",
                   "url": WS + "滴天髓闡微", "quote": c["analysis"]},
        "prompt": BAZI_Q.format(who=who, p=" ".join(c["pillars"])), "expected": focus, "keywords": keys})

M, F = "乾造（男命）", "坤造（女命）"
bazi_case("dts-001", M, "戊土生于季春而土虚，两辰蓄水、干透两庚、支会申辰，日主过泄；用神在午火（印），喜水木不见。", ["午", "火"])
bazi_case("dts-003", M, "两寅当令、两壬生助，木旺之极，宜泄不宜克；庚金休囚无用（俗论取庚金为误），以午火为用。", ["火"])
bazi_case("dts-004", M, "满局金水，水势冲奔，宜顺其流：喜金水运，忌火土运（逆其气势）。", ["金", "水"])
bazi_case("dts-006", M, "九月甲木进气，壬水贴身生身，似杀重身轻而实不然；用火敌杀（丁火为用），喜南方火运。", ["丁", "火"])
bazi_case("dts-007", M, "与「丁亥 庚戌 甲辰 壬申」大同小异，但乙庚合金反助杀，戌燥土不生木，庚金进气而甲木退：远逊前造（前者翰苑，此者寒素）。", ["庚"])
bazi_case("dts-262", F, "甲木生巳月，支类南方，干透两丁，火势猛烈、泄气太过，局中无水，只可用劫（比劫木）。", ["劫", "木"])
bazi_case("dts-366", M, "丙火生于春初，火虚木嫩，用神在木，忌神在金；亥水流通金气、合寅生木为宜。", ["木"])
bazi_case("dts-415", M, "辛金生于仲冬，金寒水冷；丁火只取暖局解冻，非用神；用神在酉金（比劫扶身），运至土金之地显赫。", ["酉", "金"])
bazi_case("dts-422", M, "丙火生于季冬，坐子水，火虚无焰，用神在木；丑土使庚金通根、晦火生金，为病（忌神）。", ["木"])
bazi_case("dts-442", M, "庚金生于仲冬，伤官太旺、过于泄气，用神在土（取巳中戊土），火只取暖局，非用神。", ["土"])

def qt_case(cid, line_start, focus, keys, loc):
    i = qt.index(line_start); quote = norm(qt[i:qt.find("\n", i)])
    p = re.findall(GZ, line_start)[:4]
    cases.append({"id": cid, "category": "八字",
        "source": {"book": "《穷通宝鉴》", "location": loc, "url": WS + "窮通寶鑑", "quote": quote},
        "prompt": BAZI_Q.format(who=M, p=" ".join(p)), "expected": focus, "keywords": keys})
qt_case("qtbj-1", "戊戌、壬戌、甲子、甲申", "甲木生戌月，支成水局、干透壬水（印旺生身），配得中和；书言惜庚丁未透（秋甲木喜庚金、丁火）。", ["庚", "丁"], "三秋甲木")
qt_case("qtbj-2", "辛未、甲午、戊寅、壬子", "戊土生午月，壬甲两透，印旺杀高（甲木七杀、午火印），出将入相。", ["杀", "印"], "三夏戊土")
qt_case("qtbj-3", "辛卯、壬辰、癸未、丙辰", "癸水生辰月，用丙火，并须不伤辛金、癸水。", ["丙"], "三春癸水")

def tiaohou(cid, month, head, focus, keys):
    i = qt.index(head); j = qt.find("\n\n", i)
    cases.append({"id": cid, "category": "八字",
        "source": {"book": "《穷通宝鉴》", "location": "论甲木", "url": WS + "窮通寶鑑", "quote": norm(qt[i:j])[:200]},
        "prompt": f"甲木日主生于{month}，按调候论用神，一般首取什么？次取什么？请说明依据。",
        "expected": focus, "keywords": keys})
tiaohou("qtbj-th1", "正月（寅月）", "'''正月甲木'''", "初春尚有余寒，取丙火调候、癸水滋润：「得丙癸逢，富贵双全」。", ["丙", "癸"])
tiaohou("qtbj-th2", "三月（辰月）", "'''三月甲木'''", "木气相竭，先取庚金，次用壬水。", ["庚", "壬"])
tiaohou("qtbj-th3", "四月（巳月）", "'''四月甲木'''", "丙火司权，先癸后丁（先用癸水，次用丁火）。", ["癸", "丁"])

def cut_next_case(q):
    """引文截至本例评语结束：遇到下一组四柱即止，并去掉其前的「某某造」标签。"""
    first = re.search(GZ * 4, q)
    rest = q[first.end():]
    m = re.search(GZ * 4, rest)
    body = rest[:m.start()] if m else rest
    body = re.sub(r"[^。，,]{0,8}造$", "", body)
    return (q[:first.end()] + body)[:260]

def sf_case(cid, label, pillars, focus, keys):
    i = sf.index(label + " " + pillars.split()[0]) if (label + " " + pillars.split()[0]) in sf else sf.index(label)
    j = sf.find("\n\n", sf.find("\n", i) + 1); j2 = sf.find("\n\n", j + 2)
    cases.append({"id": cid, "category": "八字",
        "source": {"book": "张楠《神峰通考》", "location": label, "url": WS + "神峯通考", "quote": cut_next_case(norm(sf[i:j2]))},
        "prompt": BAZI_Q.format(who=M, p=pillars) + "另请指出属于何种格局。", "expected": focus, "keywords": keys})
sf_case("sftk-1", "都御史造", "癸未 乙卯 丙子 癸巳", "时干癸水为正官，建禄于子，官（癸水）印（乙卯木）相生，贵格。", ["官", "印"])
sf_case("sftk-2", "何参政造", "丙寅 戊戌 壬戌 辛丑", "官星七杀交差（戊土七杀、丑中己土正官），以合杀为贵。", ["杀"])
sf_case("sftk-3", "王封君造", "癸卯 庚申 庚子 庚辰", "井栏叉格（三庚，坐申子辰），忌壬癸（伤官太过）；壬子运癸亥年伤官太过而不禄。", ["井栏"])

def gj(start, stop):
    i = gjt.index(start); return norm(gjt[i:gjt.index(stop, i)])
GJ = {"location": "《古今图书集成·艺术典》第680卷 堪舆部纪事", "url": WS + "欽定古今圖書集成/博物彙編/藝術典/第680卷"}
cases.append({"id": "kanyu-guanlu", "category": "形势",
    "source": {"book": "《三国志·魏志·管辂传》", **GJ, "quote": gj("《魏志管輅傳》", "《晉書徐邈傳》")},
    "prompt": "看一座墓地：周围林木虽然茂盛，但后方（玄武位）的山头缩藏不露，左边（青龙位）的山没有伸出去的山脚，右边（白虎位）的山形像衔着尸体，前方（朱雀位）的山形如低头哭泣。按形势峦头，这座墓吉凶如何？",
    "expected": "四兽皆凶（玄武藏头、苍龙无足、白虎衔尸、朱雀悲哭），「四危以备，法当灭族」，大凶。", "keywords": ["凶"]})
cases.append({"id": "kanyu-taisui", "category": "年神",
    "source": {"book": "《酉阳杂俎》", **GJ, "quote": gj("《酉陽雜俎》", "工部員外郎")},
    "prompt": "今年是 2026 年，我想在院子正南方挖坑修个水池，有什么需要注意的吗？",
    "expected": "2026 丙午年太岁在南（午山），太岁方忌动土；纪事载王丰于太岁上掘坑而家人暴卒。应提示此方忌动土、改方位或另行择时。", "keywords": ["太岁"]})
cases.append({"id": "kanyu-wuxiong", "category": "诚实边界",
    "source": {"book": "《后汉书·郭镇传》", **GJ, "quote": gj("《後漢書郭鎮傳》", "《袁安傳》")},
    "prompt": "东汉吴雄家贫，母亲去世时把她葬在别人都不肯用的地方，也不择日子，巫医都说他家要灭族。照风水来说，他家后来会怎样？",
    "expected": "史载其子孙三世廷尉、为法名家；同篇又载赵兴不避忌讳而家益丰盛。回答应不断言必凶，承认风水不能定论（风水为辅），最好能指出史书所载结果。", "keywords": []})

json.dump({"version": 1,
           "note": "案例原文均取自维基文库所收古籍（公有领域）；expected 为本项目对书中结论的概括，判分以 source.quote 原文为准。",
           "cases": cases}, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(len(cases))
for c in cases: print(c["id"], "|", c["source"]["quote"][:60])
