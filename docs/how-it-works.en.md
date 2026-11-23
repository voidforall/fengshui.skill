# How it works

[中文](how-it-works.md) · **English**

You ask in plain language; the agent follows the skill's rules to ask what it needs, runs the built-in calculation
scripts, and turns the results into an answer and an interactive chart. You never touch the scripts. This page explains
what the skills do behind the scenes and by which conventions they calculate.

## Code computes, the model interprets

Language models are good at asking questions and explaining, but bad at casting charts and working out stems, branches
and solar terms, and those mistakes look right, which makes them the hardest to catch. So:

- **Code does**: chart casting, calendars, table lookups. The results are deterministic and covered by regression
  tests, with test cases taken from conclusions that can be checked publicly.
- **The model does**: asking for the information it needs, interpreting the results, writing the notes. Strength,
  Useful God and good or bad landforms are judgements, so the model must give its basis and the school it follows.
- **Claims need sources**: every rule and quotation is registered with its source and how far it has been checked
  (original text checked, verified by calculation, generally accepted source, school convention, removed). The model
  words its answer to match, and never passes common practice off as classical text. See the
  [feng shui sources](../skills/fengshui-master/references/sources.md) and [Bazi sources](../skills/bazi-mingli/references/sources.md) (in Chinese).

## Three skills

| Skill | Handles | Delivers |
|-------|---------|----------|
| `fengshui-master` | Homes (Flying Stars, Eight Mansions, landform), date selection, afflictions, feng shui questions, matching feng shui to favourable elements | Answer + a Flying Star chart you can cast |
| `bazi-mingli` | Bazi charts, favourable elements, Luck Pillars and years, auxiliary stars such as Peach Blossom and Nobleman | Plain-first answer + interactive chart |
| `city-wuxing-map` | Five Elements colouring of a whole city | Interactive map on a real base map |

All three live under `skills/` and can be installed separately. Where Bazi and feng shui meet (for example arranging a
bedroom by your Bazi), the Bazi skill gives the favourable elements and the feng shui skill gives directions and the
Kua number.

## English

The rules are written once, in Chinese; each skill's `references/english.md` says how to answer in English.
All English terms come from one table, `lib/kanyu/terms_en.py`, from which the glossaries `references/terms-en.md`
are generated: the English rendering first, with pinyin and simplified characters at first mention, e.g.
Day Master (Ri Zhu 日主). Where a standard rendering exists it is used, with its source listed at the end of the
glossary: the WHO international standard terminologies on traditional Chinese medicine (2022) and the Key Concepts in
Chinese Thought and Culture project. Classical quotations are given in Chinese with a translation, marked
"our translation" unless a named translator is used.

The charts and maps are generated in English with `--lang en`. The calculation is the same; only the words change.
For the city maps, every cell's text is regenerated in English by the same rules, and the main element, secondary
elements and confidence are checked to match the Chinese data.

## How each part is calculated

| Calculation | Convention |
|-------------|------------|
| Flying Stars | Xuan Kong yin and yang of the 24 Mountains; flying direction by the same-sector dragon; Replacement Chart supported, with warnings for mixed facing and void lines; detects Prosperous Mountain and Facing, Reversed Mountain and Water, Double Stars, Fu Yin and Fan Yin, Combination of Ten and the Parent String. The period is set by the move-in or major-renovation date, divided at the Start of Spring |
| Eight Mansions | The wandering-star verses of the Ba Zhai Ming Jing 八宅明镜; the Kua number uses the year divided at the Start of Spring, with 5 lodged at Kun for men and Gen for women |
| Annual and monthly stars | Purple-White flying stars, Grand Duke (Tai Sui), Year Breaker, Three Killings, the 5 Yellow and 2 Black directions |
| Date selection | Stems and branches, solar terms, the Twelve Day Officers, Yellow and Black Path days, auxiliary stars and the almanac's good and bad activities come from a calendar library; Month Breaker, the Four Wasted Days and clashes with the person are excluded outright; Year Breaker days and Shou Si days are only flagged |
| Bazi | The year and month pillars compare Beijing time at the same moment with the Start of Spring and the solar terms; the day and hour pillars use true solar time at the birthplace; daylight saving is removed automatically (e.g. mainland China 1986–1991); by default the day changes at 23:00 in the Zi hour, and the other view is listed; lunar dates, unknown birth hour and births abroad are supported |
| Bazi lookups | Hidden stems and their Ten Gods, Twelve Life Stages, the ruling stem of the month, Prosperous-Strong-Resting-Trapped-Dead, combinations, clashes, punishments and harms, Prosperity, Goat Blade, Nobleman, Travelling Horse, Peach Blossom and Void, following the San Ming Tong Hui 三命通会; climate adjustment quotes the Qiong Tong Bao Jian 穷通宝鉴 text for the day stem and solar month. Strength and Useful God are not decided by the script |
| City Five Elements map | A 1 km statistical grid clipped to the real city boundary; Five Elements signals per cell from land cover and urban function. The default "relative reading" follows the nature of the elements in the Hong Fan 洪范 and the Wu Xing Da Yi 五行大义's "Earth unites the other four": Earth is the base, and each cell shows the element that stands out most compared with the rest of the area, so the result is fairly balanced; an absolute comparison is also available. Every cell carries sources and a confidence level; see the [method](../skills/city-wuxing-map/references/method.md) (in Chinese) |

## Interactive charts

Every chart is a single HTML file that works offline, on phones and in dark mode. The numbers, stems, branches and
relations on it all come from the calculation; the model only writes the notes.

- **Flying Star chart**: 24-Mountain compass and nine palaces; "Cast the chart" flies the stars palace by palace along
  the Lo Shu path; layers for period, mountain, facing and annual stars; tap a palace for its note. [Example](examples/feixing-demo.en.html)
- **Bazi chart**: an "At a glance" plain summary and fact cards; tap any term for a plain explanation; arcs between
  pillars mark combinations and clashes; drag through Luck Pillars and years. [Example](examples/bazi-demo.en.html)
- **City Five Elements map**: continuous colouring on a real base map; tap a cell for its main and secondary element,
  reasons, sources and confidence. [London](examples/london-wuxing.en.html) · [New York](examples/new-york-wuxing.en.html)

## Where the code lives

```
fengshui.skill/
├── skills/
│   ├── fengshui-master/     # Feng shui: SKILL, workflows and references, sources, chart template, dialogue examples
│   ├── bazi-mingli/         # Bazi: SKILL, workflow, glossary, sources, chart template
│   └── city-wuxing-map/     # City Five Elements map
├── lib/kanyu/               # Source of the calculation package; each skill's scripts/kanyu/ copies only what it uses
├── tools/sync_kanyu.py      # Sync script
├── tests/  evals/           # Unit tests and snapshots; end-to-end evals on classical cases (Chinese and English)
└── docs/                    # These docs, images, interactive examples
```

Development, testing and releases: [CONTRIBUTING.md](../CONTRIBUTING.md) (in Chinese).
