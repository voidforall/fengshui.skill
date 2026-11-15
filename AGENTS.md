# Working in this repository

- Never add an agent name as a commit co-author.
- Prefer quality, simplicity, robustness and maintainability over development cost. For one-off operations, use a direct path before adding automation.
- Read `SKILL.md` for the main skill and `skills/city-wuxing-map/SKILL.md` for city maps. Keep domain claims consistent with `references/sources.md`; clearly distinguish classical rules from modern interpretation.
- Calculations belong in deterministic scripts. Do not replace them with model arithmetic or invent geographic evidence.
- Reproduce product bugs through the end-user flow before fixing them. Inspect real rendered pages, including mobile layouts, and fix obvious visual defects.
- Run `python -m unittest discover -s tests -v`. City-map topology checks require `skills/city-wuxing-map/requirements.txt`; raster rebuilds additionally require `requirements-build.txt` in that skill directory.
- Regenerate committed example HTML after template or input changes; commands are in `docs/examples/README.md`. Preserve third-party map/data attribution. City examples must cover the complete declared scope, with no missing classifications.
- Record changes under `CHANGELOG.md` → Unreleased. Keep release versions synchronized only when actually releasing; the documented CI workflow validates skill packaging and Python compatibility.

Keep this file useful to almost every future session. Rewrite or prune rather than append; point to authoritative files instead of duplicating them.
