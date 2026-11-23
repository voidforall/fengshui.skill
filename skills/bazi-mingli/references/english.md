# Answering in English

Read this when the user writes in English or asks for English. It covers language only: the reading order,
scripts and source rules of this skill stay exactly the same, and the Chinese reference files remain the authority.

## Language and terms

- Answer entirely in English. Do not mix in untranslated Chinese sentences.
- Use the names in terms-en.md (in this folder). English rendering first; on the first mention add pinyin and the
  simplified characters, then use English only: "Day Master (Ri Zhu 日主)", later "Day Master".
- Write stems and branches as "Jia 甲 (Yang Wood)" and "Zi 子 (Rat)"; write a pillar as "Geng-Wu 庚午".
- Do not invent other English names. If the user uses another common name (for example "Useful God" vs
  "favorable element", "Luck Pillar" vs "Decade Luck"), acknowledge it and map it to ours.
- Script output is in Chinese. Translate it with terms-en.md; keep dates, ages and percentages exactly as printed.
  Never paste raw Chinese output into the answer.
- Birth time questions (daylight saving time, true solar time, the 23:00 day change) matter as much in English;
  explain them in plain words.

## Plain English first

Most English-speaking users know even less of the terminology than Chinese users. Follow the plain-language order
of the playbook: one-sentence conclusion, what your chart is like, two or three reasons with each term explained once,
these years, then technical details last.

- Ten Gods are metaphors, not fate: "Direct Wealth (steady income)", "Seven Killings (pressure and drive)".
- For the Twelve Life Stages use the plain column of terms-en.md: say "the Day Master is at its weakest here",
  not "the Day Master is in Death".
- "Which element am I missing" deserves the same answer as in Chinese: a count of zero does not mean you must add it.

## Quoting classics

- Quote the Chinese original exactly as recorded in sources.md, then give an English rendering.
- If you use a published translation, name the translator and year. Otherwise mark it "(our translation)".
  Never present a paraphrase as a quotation, and do not recite the Qiongtong Baojian from memory: quote the passage
  the script printed.
- Keep the source-status wording of SKILL.md in English (✅ "says", 📖 "according to the commonly cited text",
  ⚖ "a common practice in the … school").

## Interactive chart page

The chart page still has Chinese labels. Tell the user so, and explain what they will see: four pillar cards
(Year, Month, Day, Hour), the "一眼看懂" plain summary at the top, and the 大运流年 (Luck Pillars and years) timeline.
Write the notes JSON in English if the user reads English.

## Boundaries

Same as SKILL.md: Bazi is a traditional way of reflecting on a life, not a prediction of fate; no statements about
death, illness outcomes or "bad marriages"; suggest a qualified professional for health, legal or financial decisions.
