# Deliberate errors for test_tools.py (each line is expected by the test; do not fix)

- unknown key: {{sNope}} and {{sKm.titel}}
- hand-written page: see P3 for the forest plot
- hand-written page with title: P2「Hormone Therapy — Recurrence-free Survival」
- builder in backticks that does not exist: `sMissingBuilder`
- literal title (note only, not an error): 「Summary」

Not errors:

- in backticks: `P4`, `{{sNope}}`, `sTitle`
- ignored by pages_ignore.txt: the P53 protein
- ignored inline: P9 <!--pages:ignore-->
- range and parts: {{sKm}}–{{sForest}}, {{sSuppTable.title}}, {{sSummary.page}}

```text
fenced: P7 {{sNope}} `sAlsoMissing`
```

<!-- pages:counts:start -->

共 4 页（节 key 和页数）：`title` 1 · `results` 3

<!-- pages:counts:end -->
