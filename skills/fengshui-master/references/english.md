# Answering in English

Read this when the user writes in English or asks for English. It covers language only: the analysis rules,
scripts and source rules of this skill stay exactly the same, and the Chinese reference files remain the authority.

## Language and terms

- Answer entirely in English. Do not mix in untranslated Chinese sentences.
- Use the names in terms-en.md (in this folder). English rendering first; on the first mention add pinyin and the
  simplified characters, then use English only: "Flying Stars (Xuan Kong Fei Xing 玄空飞星)", later "Flying Stars".
- Do not invent other English names. If the user uses a different common name (for example "Water Star" for the
  Facing Star, or "Kua number"), acknowledge it and map it to ours.
- Script output is in Chinese. Translate it with terms-en.md; keep numbers, degrees and dates exactly as printed.
  Never paste raw Chinese output into the answer.
- Directions: give compass degrees and the English direction; name a mountain as "Zi (子), 352.5°–7.5°".
- Dates: Gregorian. When a rule depends on solar terms, say so ("the feng shui year starts at Start of Spring,
  around 4 February, not at Chinese New Year").

## Quoting classics

- Quote the Chinese original exactly as recorded in sources.md, then give an English rendering.
- If you use a published translation, name the translator and year. Otherwise mark it "(our translation)".
  Never present a paraphrase as a quotation.
- Keep the source-status wording of SKILL.md in English:
  ✅ "The Zangshu says: …"; 📖 "According to the commonly cited text of …"; ⚖ "A common practice in the … school is …";
  ✂ do not use, and say no classical source was found if asked.

## Shape of the answer

1. One-sentence conclusion in plain English.
2. What the chart or calendar shows, with each term explained once.
3. Practical suggestions.
4. Technical details last (chart numbers, school differences).

## Interactive chart pages

Add `--lang en` to the `feixing ... --html` command: the page is then in English, with terms from `terms-en.md`,
mountains in pinyin with compass codes (e.g. Zi (N2)), and the Shuo Gua quotes in Chinese with our translation.
Write the notes JSON in English too (same keys: `summary`, `palaces` keyed by the Chinese palace names 坎坤震巽中乾兑艮离,
`advice`). In the reply, point the user to the Cast the chart button and to tapping a palace for its note.

## Boundaries

Same as SKILL.md: present feng shui as a cultural tradition and a way of looking at a space, not a guarantee;
no fear-based claims, no selling of objects; for health, legal or financial decisions suggest a qualified professional.
