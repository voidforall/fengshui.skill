# Answering in English

Read this when the user writes in English or asks for English. The method, data rules and honesty rules of this
skill stay exactly the same; this file covers language only.

## Terms

| 中文 | English |
|------|---------|
| 五行 | Five Elements (Wu Xing 五行) |
| 金 木 水 火 土 | Metal, Wood, Water, Fire, Earth |
| 主象 / 兼象 | main element / secondary element |
| 相对取象 | relative reading (what stands out compared with the rest of the area) |
| 综合取象（绝对） | absolute reading (which signal is strongest in the cell) |
| 土地覆盖底层 | land-cover reading |
| 置信等级 中 / 低 | confidence: medium / low |
| 统计单元 | analysis cell (1 km grid) |
| 主城区 / 全城 | central districts / whole city |

On the first mention write "Five Elements (Wu Xing 五行)"; afterwards use English only.

## Explaining the method

- The default relative reading treats Earth as the base layer and asks which element stands out in a cell compared
  with the rest of the mapped area. It does not say that element makes up most of the cell, and readings cannot be
  compared between cities.
- The classical basis can be quoted in Chinese with an English rendering, marked as our translation. Name the
  text as "The Grand Rules" (Hong Fan 洪范) in The Book of History (Shang Shu 尚书), the renderings used by the
  state-sponsored Key Concepts in Chinese Thought and Culture project (chinesethought.cn):
  《尚书·洪范》「水曰润下，火曰炎上，木曰曲直，金曰从革，土爰稼穑」 — "Water moistens and descends, fire blazes
  upward, wood bends and straightens, metal yields and is reshaped, earth receives sowing and harvest" (our translation).
- Mapping commerce to Metal or retail and entertainment to Fire is a modern analogy; say so.

## Map page

Generate the page with `--lang en` (`python3 scripts/generate.py --example london --lang en --output ...`). Every cell's
reason, facts, limits and confidence note are then regenerated in English by the same rules, and the main element,
secondary elements and confidence are checked to be identical to the Chinese data. City, area and district names come
from the data's `en` object (for Shanghai, Hanyu Pinyin with translated generic terms, e.g. "Lujiazui Subdistrict,
Pudong New Area"). Data you write yourself without `metrics` cannot be regenerated: write its text in English and add
`"lang": "en"` (see data-format.md). Explain the controls: Reading (relative, combined, land-cover base), the element
filters, the search box, and the cell details (main and secondary element, reasons, sources, confidence).

## Boundaries

The colors are a published interpretation model, not measured energy, and say nothing about the fortune of any
home or person.
