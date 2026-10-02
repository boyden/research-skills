"""Tests of engine/tools/pages.py and engine/tools/pull_notes.py (standard library unittest).

Run from anywhere:

    python3 skills/results-deck/engine/tools/tests/test_tools.py -v

Fixtures (v2 deck layout, SPEC.md §2):
  fixture_deck/  deck.config.js (lang "zh") + output/fixture_deck_wip.pages.json (the template keys) +
                 slides/<key>.js stub page files + notes/ + outline/ (README.md and 01_results.md copied
                 from engine/template/outline/, and 02_bad.md with deliberate errors) + pages_ignore.txt.
  pptx_deck/     deck.config.js + output/results_examples_wip.pages.json derived by hand from
                 examples/slides/output/results_examples.pptx, notes/_aliases.json and two old notes
                 files (notes/sRoc.md outdated, notes/sRemoved.md of a page that is gone).
No test builds a pptx; the pull_notes tests read the example pptx of the repository.
Every test that writes works on a copy in a temporary directory.
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TESTS = Path(__file__).resolve().parent
TOOLS = TESTS.parent
ENGINE = TOOLS.parent
REPO = ENGINE.parents[2]
PAGES = TOOLS / "pages.py"
PULL = TOOLS / "pull_notes.py"
FIXTURE = TESTS / "fixture_deck"
PPTX_DECK = TESTS / "pptx_deck"
PPTX = REPO / "examples" / "slides" / "output" / "results_examples.pptx"
TEMPLATE = ENGINE / "template"
TEMPLATE_OUTLINE = TEMPLATE / "outline"
DUP = "Clinical Factors — Univariate Cox"
ZH_HEADER = "| 页 | 节 | 小节 | 页标题 | key | Note |"
EN_HEADER = "| Page | Section | Subsection | Slide title | key | Note |"
V1_HEADER = "| 页 | 节 | 小节 | 页标题 | key（builder） | Note |"

sys.dont_write_bytecode = True          # no __pycache__ next to the tools
sys.path.insert(0, str(TOOLS))
import pages as pg  # noqa: E402  # pyright: ignore[reportMissingImports]
import pull_notes  # noqa: E402  # pyright: ignore[reportMissingImports]


def run(tool, *args):
    return subprocess.run([sys.executable, "-B", str(tool), *map(str, args)], capture_output=True,
                          text=True, encoding="utf-8")


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path, data):
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def set_lang(deck, lang):
    """Set (or, with None, remove) the ``lang:`` line of a deck's deck.config.js."""
    cfg = deck / "deck.config.js"
    text = re.sub(r'^\s*lang:.*\n', "", cfg.read_text(encoding="utf-8"), flags=re.M)
    if lang is not None:
        text = text.replace("module.exports = {\n", f'module.exports = {{\n  lang: "{lang}",\n', 1)
    cfg.write_text(text, encoding="utf-8")


class TempDeck:
    """Copy of a fixture deck in a temporary directory (context manager -> Path)."""

    def __init__(self, src):
        self.src = src

    def __enter__(self):
        self.tmp = tempfile.TemporaryDirectory()
        dst = Path(self.tmp.name) / self.src.name
        shutil.copytree(self.src, dst)
        return dst

    def __exit__(self, *exc):
        self.tmp.cleanup()


# --------------------------------------------------------------------------- pages.py
class PagesCheck(unittest.TestCase):
    def test_bad_file_errors(self):
        r = run(PAGES, FIXTURE, "--check")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        out = r.stdout
        for expected in [
            "outline/02_bad.md:3  {{sNope}} is not a slide key",
            "outline/02_bad.md:3  {{sKm.titel}} is not a token",
            "outline/02_bad.md:4  hand-written page reference P3",
            "outline/02_bad.md:5  hand-written page reference P2",
            "outline/02_bad.md:6  `sMissingBuilder` is neither in pages.json nor a page file "
            "slides/sMissingBuilder.js",
            "generated block is out of date",
            "Summary: [k] 2, [r] 2, [b] 1, [g] 1  | total 6",
        ]:
            self.assertIn(expected, out)
        # literal / ignored / fenced spans are not errors; the template files are clean
        for absent in ["P4", "P53", "P9", "P7", "sAlsoMissing", "README.md:", "01_results.md:"]:
            self.assertNotIn(absent, out.split("\n[k]", 1)[1].replace("Summary:", ""), absent)

    def test_template_outline_is_clean(self):
        with TempDeck(FIXTURE) as deck:
            shutil.rmtree(deck / "outline")
            shutil.copytree(TEMPLATE_OUTLINE, deck / "outline")
            template_lang = pg.config_field(TEMPLATE, "lang", "") if (TEMPLATE / "deck.config.js").is_file() else ""
            if template_lang:                   # the outline's language follows the template's config
                set_lang(deck, template_lang)
            r = run(PAGES, deck)            # --check is the default mode
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("total 0", r.stdout)

    def test_fixture_copy_matches_template(self):
        for name in ("README.md", "01_results.md"):
            self.assertEqual((FIXTURE / "outline" / name).read_text(encoding="utf-8"),
                             (TEMPLATE_OUTLINE / name.replace(".md", ".zh-CN.md")).read_text(encoding="utf-8"),
                             f"fixture_deck/outline/{name} differs from the Chinese template outline: copy it again")

    def test_builder_check_uses_page_files(self):
        with TempDeck(FIXTURE) as deck:
            (deck / "slides" / "sExtra.js").write_text("module.exports = {};\n", encoding="utf-8")
            (deck / "slides" / "_lib").mkdir()
            (deck / "slides" / "_lib" / "sLib.js").write_text("module.exports = {};\n", encoding="utf-8")
            (deck / "slides" / "_sHidden.js").write_text("module.exports = {};\n", encoding="utf-8")
            # a function name inside a page file is not a key any more (v1 scanned for it)
            (deck / "slides" / "sKm.js").write_text("function sInsideOnly() {}\nmodule.exports = {};\n",
                                                    encoding="utf-8")
            (deck / "slides" / "sSummary.js").unlink()          # still a key of pages.json
            (deck / "outline" / "02_bad.md").unlink()
            (deck / "outline" / "03_b.md").write_text(
                "page file only: `sExtra`; pages.json only: `sSummary`; inside a file: `sInsideOnly`; "
                "_lib: `sLib`; helper: `sHidden`\n", encoding="utf-8")
            r = run(PAGES, deck, "--check")
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn("Summary: [k] 0, [r] 0, [b] 3, [g] 0", r.stdout)
            for name in ("sInsideOnly", "sLib", "sHidden"):
                self.assertIn(f"`{name}` is neither in pages.json nor a page file slides/{name}.js", r.stdout)
            for name in ("sExtra", "sSummary"):
                self.assertNotIn(f"`{name}` is neither", r.stdout)

    def test_missing_pages_is_fatal(self):
        r = run(PAGES, FIXTURE, "--pages", FIXTURE / "output" / "nope.pages.json")
        self.assertEqual(r.returncode, 2)
        self.assertIn("FATAL: pages file not found", r.stderr)

    def test_missing_config_without_pages_is_fatal(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = run(PAGES, tmp, "--keys")
            self.assertEqual(r.returncode, 2)
            self.assertIn("deck.config.js not found", r.stderr)

    def test_bad_lang_is_fatal(self):
        with TempDeck(FIXTURE) as deck:
            set_lang(deck, "fr")
            r = run(PAGES, deck, "--keys")
            self.assertEqual(r.returncode, 2)
            self.assertIn("lang must be one of 'en', 'zh', not 'fr'", r.stderr)


class PagesShowKeys(unittest.TestCase):
    def test_show_expands_tokens(self):
        r = run(PAGES, FIXTURE, "--show", "02_bad.md")
        self.assertEqual(r.returncode, 1)                   # {{sNope}} stays unresolved
        self.assertIn("unknown keys left unresolved: sNope", r.stderr)
        out = r.stdout
        self.assertIn("P2「Hormone Therapy — Recurrence-free Survival」–P3「Clinical Factors — Univariate Cox」", out)
        self.assertIn(", Supplementary — Cohort Characteristics, P4", out)
        self.assertIn("in backticks: `P4`, `{{sNope}}`, `sTitle`", out)       # literal
        self.assertIn("fenced: P7 {{sNope}}", out)

    def test_show_readme_note_tokens(self):
        r = run(PAGES, FIXTURE, "--show", "outline/README.md")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("抄自 P2「Hormone Therapy — Recurrence-free Survival」、P3「Clinical Factors — Univariate Cox」、"
                      "P5「Supplementary — Cohort Characteristics」。", r.stdout)
        self.assertIn("P1「Title」–P5「Supplementary — Cohort Characteristics」", r.stdout)

    def test_keys(self):
        r = run(PAGES, FIXTURE, "--keys")
        self.assertEqual(r.returncode, 0, r.stderr)
        lines = r.stdout.splitlines()
        self.assertEqual(len(lines), 6)
        self.assertEqual(lines[0].split(), ["page", "key", "section", "title"])   # order is not shown
        self.assertEqual(lines[2].split()[:4], ["2", "sKm", "results", "Hormone"])
        self.assertTrue(lines[5].endswith("Supplementary — Cohort Characteristics"))

    def test_repeated_titles_warn(self):
        with TempDeck(FIXTURE) as deck:
            pj = deck / "output" / "fixture_deck_wip.pages.json"
            rows = read_json(pj)
            rows.insert(3, {"page": 4, "title": rows[2]["title"], "section": "results", "order": 30,
                            "builder": "sForestBis"})
            for i, row in enumerate(rows, 1):
                row["page"] = i
            write_json(pj, rows)
            r = run(PAGES, deck, "--keys")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("WARNING: titles shared by several pages", r.stderr)
            self.assertIn("pages [3, 4]", r.stderr)
            self.assertIn("   4  sForestBis", r.stdout)
            (deck / "outline" / "03_dup.md").write_text("see {{sForestBis}} and {{sForestBis.title}}\n",
                                                        encoding="utf-8")
            r = run(PAGES, deck, "--show", "03_dup.md")
            self.assertEqual(r.stdout, "see P4「Clinical Factors — Univariate Cox」 and Clinical Factors — Univariate Cox\n")

    def test_repeated_key_is_fatal(self):
        # v2: key = page file name, so a key on two pages is a broken pages.json (no more name#2)
        with TempDeck(FIXTURE) as deck:
            pj = deck / "output" / "fixture_deck_wip.pages.json"
            rows = read_json(pj)
            rows.insert(3, {"page": 4, "title": "Another", "section": "results", "order": 30, "builder": "sForest"})
            for i, row in enumerate(rows, 1):
                row["page"] = i
            write_json(pj, rows)
            r = run(PAGES, deck, "--keys")
            self.assertEqual(r.returncode, 2)
            self.assertIn("keys must be unique", r.stderr)
            self.assertIn("sForest on pages [3, 4]", r.stderr)

    def test_repeated_page_number_is_fatal(self):
        with TempDeck(FIXTURE) as deck:
            pj = deck / "output" / "fixture_deck_wip.pages.json"
            rows = read_json(pj)
            rows[1]["page"] = 1
            write_json(pj, rows)
            r = run(PAGES, deck, "--keys")
            self.assertEqual(r.returncode, 2)
            self.assertIn("page number 1 appears twice", r.stderr)


class PagesTable(unittest.TestCase):
    @staticmethod
    def add_new_slide(deck):
        pj = deck / "output" / "fixture_deck_wip.pages.json"
        rows = read_json(pj)
        rows.insert(2, {"page": 0, "title": "New Slide", "section": "results", "order": 15, "builder": "sNew"})
        for i, row in enumerate(rows, 1):
            row["page"] = i
        write_json(pj, rows)

    def test_table_dry_run_and_write(self):
        with TempDeck(FIXTURE) as deck:
            pj = deck / "output" / "fixture_deck_wip.pages.json"
            readme = deck / "outline" / "README.md"
            original = readme.read_text(encoding="utf-8")
            rows = read_json(pj)
            rows = [r for r in rows if r["builder"] != "sSummary"]          # drop a slide
            rows[1]["title"] = "Tamoxifen — Recurrence-free Survival"         # rename a slide
            rows.insert(2, {"page": 0, "title": "New Slide", "section": "results", "order": 15, "builder": "sNew"})
            for i, row in enumerate(rows, 1):
                row["page"] = i
            write_json(pj, rows)

            r = run(PAGES, deck, "--table")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("DRY RUN", r.stdout)
            self.assertIn("outline/README.md: keys in the table that are no longer slides", r.stdout)
            self.assertIn("sSummary", r.stdout)
            self.assertIn("+| P3 | results | — | New Slide | `sNew` | （待补 Note） |", r.stdout)
            self.assertEqual(readme.read_text(encoding="utf-8"), original)
            self.assertFalse((deck / ".backups").exists())

            r = run(PAGES, deck, "--table", "--write")
            self.assertEqual(r.returncode, 0, r.stderr)
            text = readme.read_text(encoding="utf-8")
            self.assertIn("共 5 页（节 key 和页数）：`title` 1 · `results` 3 · `supplementary` 1", text)
            self.assertIn("| P2 | results | 1.1 | Tamoxifen — Recurrence-free Survival | `sKm` | tamoxifen 与无", text)
            self.assertIn("| P3 | results | — | New Slide | `sNew` | （待补 Note） |", text)
            self.assertIn("| P4 | results | 1.2 | Clinical Factors — Univariate Cox | `sForest` |", text)
            self.assertNotIn("`sSummary` |", text)
            backups = list((deck / ".backups").glob("*/outline/README.md"))
            self.assertEqual(len(backups), 1)
            self.assertEqual(backups[0].read_text(encoding="utf-8"), original)
            self.assertTrue(list((deck / ".backups").glob("*/outline/02_bad.md")))

            r = run(PAGES, deck, "--table")
            self.assertIn("outline/README.md: generated blocks up to date", r.stdout)
            r = run(PAGES, deck, "--check")
            self.assertEqual(r.returncode, 1)
            self.assertIn("{{sSummary}} is not a slide key", r.stdout)      # the prose still names it
            self.assertNotIn("[g]", r.stdout.split("Summary:")[0])

    def test_lang_en_blocks(self):
        for lang in ("en", None):                       # None: no lang line, "en" is the default
            with self.subTest(lang=lang), TempDeck(FIXTURE) as deck:
                set_lang(deck, lang)
                self.add_new_slide(deck)
                readme = deck / "outline" / "README.md"
                r = run(PAGES, deck, "--table", "--write")
                self.assertEqual(r.returncode, 0, r.stderr)
                text = readme.read_text(encoding="utf-8")
                self.assertIn("\n6 slides (section key and slide count): "
                              "`title` 1 · `results` 3 · `summary` 1 · `supplementary` 1\n", text)
                self.assertIn(EN_HEADER, text)
                self.assertNotIn(ZH_HEADER, text)
                self.assertIn("| P3 | results | — | New Slide | `sNew` | (Note to be added) |", text)
                self.assertIn("| P2 | results | 1.1 | Hormone Therapy — Recurrence-free Survival | `sKm` | "
                              "tamoxifen 与无", text)                  # hand-written cells are kept
                self.assertNotIn("共 ", text.split("<!-- pages:counts:start -->")[1].split("<!-- pages:counts:end -->")[0])
                r = run(PAGES, deck, "--check")
                self.assertIn("[g] 0", r.stdout)

    def test_lang_zh_blocks(self):
        with TempDeck(FIXTURE) as deck:
            self.add_new_slide(deck)
            r = run(PAGES, deck, "--table", "--write")
            self.assertEqual(r.returncode, 0, r.stderr)
            text = (deck / "outline" / "README.md").read_text(encoding="utf-8")
            self.assertIn("\n共 6 页（节 key 和页数）：`title` 1 · `results` 3 · `summary` 1 · `supplementary` 1\n", text)
            self.assertIn(ZH_HEADER, text)
            self.assertIn("| P3 | results | — | New Slide | `sNew` | （待补 Note） |", text)

    def test_header_language_switch(self):
        with TempDeck(FIXTURE) as deck:
            readme = deck / "outline" / "README.md"
            self.add_new_slide(deck)
            self.assertEqual(run(PAGES, deck, "--table", "--write").returncode, 0)
            zh_text = readme.read_text(encoding="utf-8")

            set_lang(deck, "en")
            r = run(PAGES, deck, "--check")
            self.assertIn("outline/README.md:", r.stdout.split("[g]", 1)[1])     # header language is stale
            self.assertEqual(run(PAGES, deck, "--table", "--write").returncode, 0)
            en_text = readme.read_text(encoding="utf-8")
            self.assertIn(EN_HEADER, en_text)
            self.assertIn("| P3 | results | — | New Slide | `sNew` | (Note to be added) |", en_text)
            self.assertNotIn("（待补 Note）|", en_text.split("<!-- pages:table:start -->")[1])
            self.assertIn("| P4 | results | 1.2 | Clinical Factors — Univariate Cox | `sForest` | 8 个临床因素", en_text)

            set_lang(deck, "zh")
            self.assertEqual(run(PAGES, deck, "--table", "--write").returncode, 0)
            self.assertEqual(readme.read_text(encoding="utf-8"), zh_text)     # round trip

    def test_v1_header_is_read(self):
        with TempDeck(FIXTURE) as deck:
            readme = deck / "outline" / "README.md"
            original = readme.read_text(encoding="utf-8")
            self.assertIn(ZH_HEADER, original)
            readme.write_text(original.replace(ZH_HEADER, V1_HEADER), encoding="utf-8")
            r = run(PAGES, deck, "--check")
            self.assertIn("outline/README.md:", r.stdout.split("[g]", 1)[1])
            r = run(PAGES, deck, "--table", "--write")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertNotIn("no longer slides", r.stdout)
            self.assertEqual(readme.read_text(encoding="utf-8"), original)

    def test_write_needs_table(self):
        r = run(PAGES, FIXTURE, "--write")
        self.assertEqual(r.returncode, 2)
        self.assertIn("--write only goes with --table", r.stderr)


# --------------------------------------------------------------------------- pull_notes.py
def notes_files(deck):
    """{name: content} of the files in <deck>/notes/."""
    return {p.name: p.read_text(encoding="utf-8") for p in sorted((deck / "notes").iterdir())}


@unittest.skipUnless(PPTX.is_file(), f"example pptx not built: {PPTX}")
class PullNotes(unittest.TestCase):
    def test_fixture_titles_match_pptx(self):
        rows = read_json(PPTX_DECK / "output" / "results_examples_wip.pages.json")
        slides = pull_notes.read_pptx(PPTX, [r["title"] for r in rows])
        self.assertEqual([s["title"] for s in slides], [r["title"] for r in rows],
                         "results_examples.pptx changed: derive pptx_deck/output/results_examples_wip.pages.json again")
        self.assertEqual([s["hidden"] for s in slides], [False] * 12 + [True])

    def test_dry_run_reports_and_writes_nothing(self):
        with TempDeck(PPTX_DECK) as deck:
            before = notes_files(deck)
            r = run(PULL, deck, PPTX, "--dry-run")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("(13 slides, 1 hidden)", r.stdout)
            self.assertIn("matched 13 slides -> 12 new, 1 changed, 0 unchanged in notes/", r.stdout)
            self.assertIn("to write (13):", r.stdout)
            self.assertIn("changed   sRoc", r.stdout)
            self.assertIn("new       sEmphasis2", r.stdout)
            self.assertIn("files of keys that are not in pages.json (kept; delete by hand if the page is gone): "
                          "sRemoved", r.stdout)
            self.assertIn("WARNING: titles shared by several pages", r.stderr)
            self.assertNotIn("notes.json", r.stdout)                    # no v1 file, no hint
            self.assertEqual(notes_files(deck), before)
            self.assertFalse((deck / "notes" / "_unmatched.json").exists())
            self.assertFalse((deck / ".backups").exists())

    def test_write_then_unchanged(self):
        with TempDeck(PPTX_DECK) as deck:
            old_roc = (deck / "notes" / "sRoc.md").read_text(encoding="utf-8")
            r = run(PULL, deck, PPTX, "--write")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("written (13):", r.stdout)
            keys = [row["builder"] for row in read_json(deck / "output" / "results_examples_wip.pages.json")]
            files = notes_files(deck)
            self.assertEqual(sorted(files), sorted([f"{k}.md" for k in keys] + ["_aliases.json", "_unmatched.json",
                                                                               "sRemoved.md"]))  # nothing deleted
            km = files["sKm.md"]
            self.assertTrue(km.startswith("PATTERN: assertion–evidence."))
            self.assertIn("\n\nDesign rules shown:", km)                          # paragraphs -> lines
            self.assertTrue(files["sEmphasis1.md"].startswith("PATTERN: progressive emphasis, step 1 of 2."))
            self.assertTrue(files["sEmphasis2.md"].startswith("PATTERN: progressive emphasis, step 2 of 2."))
            self.assertTrue(files["sForest.md"].startswith("PATTERN: forest plot"))
            for key in keys:
                text = files[f"{key}.md"]
                self.assertTrue(text.endswith("\n") and not text.endswith("\n\n"), key)   # one trailing newline
                self.assertTrue(all(line == line.rstrip() for line in text.split("\n")), key)
                self.assertNotIn("\r", text)
            self.assertEqual(files["_unmatched.json"], "[]\n")
            backups = sorted(p.relative_to(deck / ".backups").as_posix()
                             for p in (deck / ".backups").rglob("*") if p.is_file())
            self.assertEqual(len(backups), 1, backups)                             # only the existing changed file
            self.assertTrue(backups[0].endswith("/notes/sRoc.md"))
            self.assertEqual(next((deck / ".backups").rglob("sRoc.md")).read_text(encoding="utf-8"), old_roc)

            r = run(PULL, deck, PPTX)
            self.assertIn("matched 13 slides -> 0 new, 0 changed, 13 unchanged", r.stdout)
            self.assertIn("unchanged (not written): sKm, sRoc, sForest", r.stdout)
            self.assertIn("DRY RUN", r.stdout)
            stamp = {p.name: p.stat().st_mtime_ns for p in (deck / "notes").iterdir()}
            r = run(PULL, deck, PPTX, "--write")
            self.assertIn("wrote 0 notes file(s)", r.stdout)
            self.assertIn("notes/_unmatched.json unchanged", r.stdout)
            self.assertEqual({p.name: p.stat().st_mtime_ns for p in (deck / "notes").iterdir()}, stamp)

    def test_only_changed_files_written(self):
        with TempDeck(PPTX_DECK) as deck:
            rows = read_json(deck / "output" / "results_examples_wip.pages.json")
            slides = pull_notes.read_pptx(PPTX, [r["title"] for r in rows])
            km, forest = deck / "notes" / "sKm.md", deck / "notes" / "sForest.md"
            # same text with CRLF and no trailing newline: unchanged, the file is left as it is
            km.write_bytes(slides[0]["notes"].replace("\n", "\r\n").encode("utf-8"))
            forest.write_text("Outdated forest notes.\n", encoding="utf-8")
            os.utime(km, ns=(1_000_000_000, 1_000_000_000))
            km_bytes = km.read_bytes()
            r = run(PULL, deck, PPTX, "--write")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("matched 13 slides -> 10 new, 2 changed, 1 unchanged", r.stdout)
            self.assertIn("unchanged (not written): sKm", r.stdout)
            self.assertIn("changed   sForest", r.stdout)
            self.assertEqual(km.read_bytes(), km_bytes)
            self.assertEqual(km.stat().st_mtime_ns, 1_000_000_000)
            self.assertTrue(forest.read_text(encoding="utf-8").startswith("PATTERN: forest plot"))
            backed = sorted(p.name for p in (deck / ".backups").rglob("*") if p.is_file())
            self.assertEqual(backed, ["sForest.md", "sRoc.md"])
            self.assertEqual(next((deck / ".backups").rglob("sForest.md")).read_text(encoding="utf-8"),
                             "Outdated forest notes.\n")

    def test_repeated_title_without_aliases_is_unmatched(self):
        with TempDeck(PPTX_DECK) as deck:
            aliases = deck / "notes" / "_aliases.json"
            saved = aliases.read_text(encoding="utf-8")
            aliases.unlink()
            r = run(PULL, deck, PPTX, "--write")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("UNMATCHED 3 slide(s) (not written; listed in notes/_unmatched.json)", r.stdout)
            self.assertIn(f"slide 8: '{DUP}' (occurrence 2) -- title occurs 3 times in the pptx", r.stdout)
            self.assertIn("pages.json keys without a matched slide (their notes files are not touched): "
                          "sForest, sEmphasis1, sEmphasis2", r.stdout)
            un = read_json(deck / "notes" / "_unmatched.json")
            self.assertEqual([u["slide"] for u in un], [3, 8, 9])
            self.assertTrue(un[1]["notes"].startswith("PATTERN: progressive emphasis, step 1 of 2."))
            for key in ("sForest", "sEmphasis1", "sEmphasis2"):
                self.assertFalse((deck / "notes" / f"{key}.md").exists())
            self.assertEqual(len(list((deck / "notes").glob("s*.md"))), 11)     # 10 matched + sRemoved

            # with the aliases back, --write rewrites _unmatched.json (and backs up the old one)
            aliases.write_text(saved, encoding="utf-8")
            r = run(PULL, deck, PPTX, "--write")
            self.assertIn("matched 13 slides -> 3 new, 0 changed, 10 unchanged", r.stdout)
            self.assertIn("notes/_unmatched.json (0 entries)", r.stdout)
            self.assertEqual(read_json(deck / "notes" / "_unmatched.json"), [])
            old = [p for p in (deck / ".backups").rglob("_unmatched.json")]
            self.assertEqual(len(old), 1)
            self.assertEqual(len(read_json(old[0])), 3)

    def test_taken_and_unknown_alias_keys(self):
        with TempDeck(PPTX_DECK) as deck:
            write_json(deck / "notes" / "_aliases.json",
                       {DUP: "sForest", f"{DUP}#2": "sForest", f"{DUP}#3": "sGhost"})
            r = run(PULL, deck, PPTX, "--write")
            self.assertIn("slide 8: '%s' (occurrence 2) -- key 'sForest' is already taken by slide 3" % DUP, r.stdout)
            self.assertIn("slide 9: '%s' (occurrence 3) -- key 'sGhost' is not in pages.json" % DUP, r.stdout)
            self.assertEqual([u["slide"] for u in read_json(deck / "notes" / "_unmatched.json")], [8, 9])
            self.assertFalse((deck / "notes" / "sGhost.md").exists())

    def test_title_slide_and_pages_override(self):
        with TempDeck(PPTX_DECK) as deck:
            rows = read_json(deck / "output" / "results_examples_wip.pages.json")
            rows[0].update(title="Title", builder="sTitle")      # a title slide never shows the word "Title"
            alt = deck / "alt.pages.json"
            write_json(alt, rows)
            r = run(PULL, deck, PPTX, "--write", "--pages", alt)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("new       sTitle", r.stdout)
            self.assertTrue((deck / "notes" / "sTitle.md").read_text(encoding="utf-8")
                            .startswith("PATTERN: assertion–evidence."))
            self.assertFalse((deck / "notes" / "sKm.md").exists())

    def test_v1_notes_json_hint(self):
        with TempDeck(PPTX_DECK) as deck:
            v1 = deck / "notes.json"
            write_json(v1, {"sRoc": "v1 notes"})
            before = v1.read_text(encoding="utf-8")
            r = run(PULL, deck, PPTX, "--write")
            self.assertEqual(r.returncode, 0, r.stderr)
            hint = [ln for ln in r.stdout.splitlines() if "notes.json" in ln]
            self.assertEqual(hint, ["NOTE: notes.json is not read: v2 keeps one notes/<key>.md per slide "
                                    "(aliases in notes/_aliases.json)"])
            self.assertEqual(v1.read_text(encoding="utf-8"), before)
            self.assertTrue((deck / "notes" / "sRoc.md").read_text(encoding="utf-8").startswith("PATTERN:"))

    def test_default_pptx_is_highest_release(self):
        with TempDeck(PPTX_DECK) as deck:
            r = run(PULL, deck)
            self.assertEqual(r.returncode, 2)
            self.assertIn("no release", r.stderr)
            shutil.copy2(PPTX, deck / "output" / "results_examples_v10.pptx")
            (deck / "output" / "results_examples_v2.pptx").write_text("not a pptx", encoding="utf-8")
            r = run(PULL, deck)
            self.assertEqual(r.returncode, 0, r.stderr)                  # v10 > v2 (numeric, not text order)
            self.assertIn("results_examples_v10.pptx (13 slides, 1 hidden)", r.stdout)

    def test_dry_run_and_write_exclusive(self):
        r = run(PULL, PPTX_DECK, PPTX, "--dry-run", "--write")
        self.assertEqual(r.returncode, 2)
        self.assertIn("not allowed with argument", r.stderr)


if __name__ == "__main__":
    unittest.main()
