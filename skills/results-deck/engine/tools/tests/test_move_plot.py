"""Tests of engine/tools/move.py and engine/tools/plot.py (standard library unittest).

Run from anywhere:

    python3 -B skills/results-deck/engine/tools/tests/test_move_plot.py -v

Fixtures:
  move_deck/  deck.config.js (sections title, results, summary, supplementary) and slides/:
              sTitle (title 10), sKm (results 10), sForest (results 20), sNodes (results 30),
              sTight (results 30.001), sSummary (summary 10); slides/_lib/ and slides/_draft.js are not
              pages; notes/sSummary.md carries order-dependent wording.
  plot_deck/  deck.config.js + theme/theme.json (dpi 40) + plotting/{__init__,style,common,a,b,_helpers}.py;
              a.py registers alpha_line and alpha_bar, b.py beta_scatter.  The figures return what
              style.py saw (DECK_THEME, DECK_FIG_DIR) in their stats.
Every test works on a copy in a temporary directory.  The plot tests are skipped when matplotlib or
numpy is not importable by this interpreter.
"""

import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TESTS = Path(__file__).resolve().parent
TOOLS = TESTS.parent
ENGINE = TOOLS.parent
MOVE = TOOLS / "move.py"
PLOT = TOOLS / "plot.py"
MOVE_DECK = TESTS / "move_deck"
PLOT_DECK = TESTS / "plot_deck"
HAVE_MPL = all(importlib.util.find_spec(m) is not None for m in ("matplotlib", "numpy"))

sys.dont_write_bytecode = True          # no __pycache__ next to the tools or in the fixtures


def run(tool, *args):
    return subprocess.run([sys.executable, "-B", str(tool), *map(str, args)], capture_output=True,
                          text=True, encoding="utf-8")


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


def snapshot(root: Path) -> dict:
    """{relative path: bytes} of every file under root."""
    return {str(p.relative_to(root)): p.read_bytes() for p in sorted(root.rglob("*")) if p.is_file()}


def changed(before: dict, after: dict) -> list:
    return sorted(k for k in set(before) | set(after) if before.get(k) != after.get(k))


# --------------------------------------------------------------------------- move.py
class MoveTests(unittest.TestCase):
    def move(self, deck, *args):
        before = snapshot(deck)
        r = run(MOVE, deck, *args)
        return r, before, snapshot(deck)

    def assert_only_fields_changed(self, old: bytes, new: bytes, replacements):
        """new == old with the given (old text, new text) replacements and nothing else."""
        expected = old.decode("utf-8")
        for a, b in replacements:
            self.assertEqual(expected.count(a), 1, a)
            expected = expected.replace(a, b)
        self.assertEqual(new.decode("utf-8"), expected)

    def test_after_moves_into_anchor_section(self):
        with TempDeck(MOVE_DECK) as deck:
            r, before, after = self.move(deck, "sSummary", "--after", "sKm")
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertEqual(changed(before, after), ["slides/sSummary.js"])
            self.assert_only_fields_changed(before["slides/sSummary.js"], after["slides/sSummary.js"],
                                            [('section: "summary"', 'section: "results"'),
                                             ("order: 10", "order: 15")])
            self.assertIn("section : summary -> results", r.stdout)
            self.assertIn("order   : 10 -> 15", r.stdout)
            self.assertIn("position: 6 -> 3 of 6", r.stdout)
            self.assertIn("build.js", r.stdout)
            self.assertIn("--only sSummary", r.stdout)
            # wording warnings: the moved page's notes and the new neighbor sKm
            self.assertIn("notes/sSummary.md:2: 'See slide'", r.stdout)
            self.assertIn("slides/sKm.js:10: 'next slide'", r.stdout)

    def test_after_within_section_keeps_quotes_and_comments(self):
        with TempDeck(MOVE_DECK) as deck:
            r, before, after = self.move(deck, "sKm", "--after", "sForest")
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertEqual(changed(before, after), ["slides/sKm.js"])
            # the commented-out "order: 99" / section: "summary" stay; only the real field changes
            self.assert_only_fields_changed(before["slides/sKm.js"], after["slides/sKm.js"],
                                            [("  order: 10,", "  order: 25,")])
            self.assertIn("section : results (unchanged)", r.stdout)

    def test_before_single_quotes(self):
        with TempDeck(MOVE_DECK) as deck:
            r, before, after = self.move(deck, "sSummary", "--before", "sForest")
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertEqual(changed(before, after), ["slides/sSummary.js"])
            self.assertIn("order   : 10 -> 15", r.stdout)
            r, before, after = self.move(deck, "sNodes", "--before", "sForest")
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            # one-line fields `section: "results", order: 30,`; between 15 and 20 the integer 18 is preferred
            self.assert_only_fields_changed(before["slides/sNodes.js"], after["slides/sNodes.js"],
                                            [("order: 30,", "order: 18,")])
            r, before, after = self.move(deck, "sTitle", "--before", "sForest")
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assert_only_fields_changed(before["slides/sTitle.js"], after["slides/sTitle.js"],
                                            [('section: "title"', 'section: "results"'),
                                             ("order: 10", "order: 19")])
            r, before, after = self.move(deck, "sSummary", "--after", "sTitle")     # between 19 and 20
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assert_only_fields_changed(before["slides/sSummary.js"], after["slides/sSummary.js"],
                                            [("order: 15", "order: 19.5")])

    def test_before_first_and_single_quoted_section(self):
        with TempDeck(MOVE_DECK) as deck:
            r, before, after = self.move(deck, "sForest", "--to", "summary", "--first")
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assert_only_fields_changed(before["slides/sForest.js"], after["slides/sForest.js"],
                                            [("section: 'results'", "section: 'summary'"),
                                             ("order: 20", "order: 0")])

    def test_to_section_last_and_empty(self):
        with TempDeck(MOVE_DECK) as deck:
            r, before, after = self.move(deck, "sKm", "--to", "supplementary")
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertEqual(changed(before, after), ["slides/sKm.js"])
            self.assertIn("order   : 10 -> 10", r.stdout)               # empty section -> 10
            self.assertIn("position: 2 -> 6 of 6", r.stdout)
            r, before, after = self.move(deck, "sNodes", "--to", "supplementary", "--last")
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("order   : 30 -> 20", r.stdout)
            r, before, after = self.move(deck, "sForest", "--to", "summary")
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("order   : 20 -> 20", r.stdout)               # after sSummary (10)

    def test_already_there_writes_nothing(self):
        with TempDeck(MOVE_DECK) as deck:
            r, before, after = self.move(deck, "sForest", "--after", "sKm")
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("already there", r.stdout)
            self.assertEqual(changed(before, after), [])

    def test_no_gap_exits_2(self):
        with TempDeck(MOVE_DECK) as deck:
            r, before, after = self.move(deck, "sKm", "--after", "sNodes")
            self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
            self.assertIn("no free order between 30 (sNodes) and 30.001 (sTight)", r.stderr)
            self.assertIn("--respace results", r.stderr)
            self.assertEqual(changed(before, after), [])

    def test_respace(self):
        with TempDeck(MOVE_DECK) as deck:
            r, before, after = self.move(deck, "--respace", "results")
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("integrator-only", r.stdout)
            # sKm 10 and sForest 20 already fit; sNodes 30 -> 30 too; only sTight changes
            self.assertEqual(changed(before, after), ["slides/sTight.js"])
            self.assert_only_fields_changed(before["slides/sTight.js"], after["slides/sTight.js"],
                                            [("order: 30.001", "order: 40")])
            # now the move that had no gap works
            r, before, after = self.move(deck, "sKm", "--after", "sNodes")
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("order   : 10 -> 35", r.stdout)

    def test_respace_after_insert(self):
        with TempDeck(MOVE_DECK) as deck:
            self.assertEqual(run(MOVE, deck, "sSummary", "--after", "sKm").returncode, 0)   # results 15
            r, before, after = self.move(deck, "--respace", "results")
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertEqual(changed(before, after), ["slides/sForest.js", "slides/sNodes.js",
                                                      "slides/sSummary.js", "slides/sTight.js"])
            orders = {k: after[f"slides/{k}.js"].decode() for k in ("sKm", "sSummary", "sForest", "sNodes", "sTight")}
            for key, value in [("sKm", "10"), ("sSummary", "20"), ("sForest", "30"), ("sNodes", "40"),
                               ("sTight", "50")]:
                self.assertRegex(orders[key], rf"order: {value},")

    def test_dry_run_writes_nothing(self):
        with TempDeck(MOVE_DECK) as deck:
            for args in (["sSummary", "--after", "sKm"], ["sKm", "--to", "supplementary"],
                         ["--respace", "results"]):
                r, before, after = self.move(deck, *args, "--dry-run")
                self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
                self.assertIn("dry run", r.stdout)
                self.assertEqual(changed(before, after), [], args)

    def test_errors(self):
        with TempDeck(MOVE_DECK) as deck:
            for args, msg in [
                (["sNope", "--after", "sKm"], "no page 'sNope'"),
                (["sKm", "--after", "sNope"], "no page 'sNope'"),
                (["sKm", "--after", "sKm"], "relative to itself"),
                (["sKm", "--to", "nowhere"], "section 'nowhere' is not in"),
                (["sKm", "--after", "sForest", "--first"], "--first / --last only go with --to"),
                (["sKm", "--respace", "results"], "--respace takes no page key"),
                (["--after", "sKm"], "give the key"),
                (["sKm"], "one of the arguments"),
            ]:
                r = run(MOVE, deck, *args)
                self.assertEqual(r.returncode, 2, args)
                self.assertIn(msg, r.stderr, args)

    def test_bad_page_files_are_listed(self):
        with TempDeck(MOVE_DECK) as deck:
            (deck / "slides" / "sBad.js").write_text('module.exports = { section: "nowhere", order: 5 };\n',
                                                    encoding="utf-8")
            (deck / "slides" / "sNoOrder.js").write_text('module.exports = { section: "results" };\n',
                                                        encoding="utf-8")
            r = run(MOVE, deck, "sKm", "--to", "summary")
            self.assertEqual(r.returncode, 2)
            self.assertIn("slides/sBad.js: section 'nowhere' is not in", r.stderr)
            self.assertIn("slides/sNoOrder.js: no numeric `order: ...` field", r.stderr)

    def test_crlf_kept(self):
        with TempDeck(MOVE_DECK) as deck:
            page = deck / "slides" / "sForest.js"
            page.write_bytes(page.read_bytes().replace(b"\n", b"\r\n"))
            old = page.read_bytes()
            r = run(MOVE, deck, "sForest", "--after", "sNodes", "--dry-run")
            self.assertEqual(r.returncode, 2)                            # sNodes/sTight: no gap
            r = run(MOVE, deck, "sForest", "--before", "sKm")
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertEqual(page.read_bytes(), old.replace(b"order: 20", b"order: 0"))


# --------------------------------------------------------------------------- plot.py
@unittest.skipUnless(HAVE_MPL, "matplotlib / numpy not importable by this interpreter")
class PlotTests(unittest.TestCase):
    def read_meta(self, fig_dir, name):
        return json.loads((fig_dir / "run_meta" / f"{name}.json").read_text(encoding="utf-8"))

    def test_only_writes_only_those(self):
        with TempDeck(PLOT_DECK) as deck:
            r = run(PLOT, deck, "--only", "alpha_line", "beta_scatter")
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            figs = deck / "figures"
            self.assertEqual(sorted(p.name for p in figs.glob("*.png")), ["alpha_line.png", "beta_scatter.png"])
            self.assertEqual(sorted(p.name for p in (figs / "run_meta").iterdir()),
                             ["alpha_line.json", "beta_scatter.json"])
            meta = self.read_meta(figs, "alpha_line")
            self.assertEqual(set(meta), {"figure", "png", "module", "stats", "inputs", "versions", "created",
                                         "theme"})
            self.assertEqual(meta["figure"], "alpha_line")
            self.assertEqual(meta["png"], "alpha_line.png")
            self.assertEqual(meta["module"], "plotting.a")
            self.assertEqual(meta["stats"]["n"], 5)                     # numpy int64 -> int
            self.assertEqual(meta["stats"]["max"], 16.0)
            self.assertIsNone(meta["stats"]["nan"])                     # NaN -> null (strict JSON)
            self.assertTrue(meta["stats"]["applied"])                   # style.apply_style() ran first
            self.assertEqual(meta["inputs"], [str(deck / "data" / "alpha.csv"), str(deck / "data" / "cohort.csv")])
            self.assertEqual(self.read_meta(figs, "beta_scatter")["inputs"],
                             ["data/beta.csv", str(deck / "data" / "cohort.csv")])
            self.assertIn("matplotlib", meta["versions"])
            self.assertIn("python", meta["versions"])
            # style.save() wrote at the theme dpi (40): HALF = 2 x 2 in -> 80 x 80 px
            png = (figs / "alpha_line.png").read_bytes()
            self.assertEqual((int.from_bytes(png[16:20], "big"), int.from_bytes(png[20:24], "big")), (80, 80))
            # a second --only run leaves the first run's files alone
            stamp = (figs / "alpha_line.png").stat().st_mtime_ns
            r = run(PLOT, deck, "--only", "alpha_bar")
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertEqual((figs / "alpha_line.png").stat().st_mtime_ns, stamp)
            self.assertEqual(self.read_meta(figs, "alpha_bar")["stats"]["bars"], [1, 2])

    def test_env_seen_by_style(self):
        with TempDeck(PLOT_DECK) as deck:
            r = run(PLOT, deck, "--only", "alpha_line")
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            meta = self.read_meta(deck / "figures", "alpha_line")
            self.assertEqual(meta["stats"]["deck_theme"], str((deck / "theme").resolve()))
            self.assertEqual(meta["stats"]["deck_fig_dir"], str((deck / "figures").resolve()))
            self.assertEqual(meta["stats"]["theme_name"], "plot_fixture")
            self.assertEqual(meta["theme"], str((deck / "theme").resolve()))

    def test_out_dir(self):
        with TempDeck(PLOT_DECK) as deck, tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "regression"
            r = run(PLOT, deck, "--only", "alpha_line", "--out-dir", out)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertFalse((deck / "figures").exists())
            self.assertTrue((out / "alpha_line.png").is_file())
            meta = self.read_meta(out, "alpha_line")
            self.assertEqual(meta["stats"]["deck_fig_dir"], str(out.resolve()))

    def test_fig_dir_and_missing_theme_from_config(self):
        with TempDeck(PLOT_DECK) as deck:
            cfg = deck / "deck.config.js"
            cfg.write_text(cfg.read_text(encoding="utf-8").replace('figDir: "figures"', 'figDir: "figs/slide"')
                           .replace('theme: "theme"', 'theme: "theme_missing"'), encoding="utf-8")
            r = run(PLOT, deck, "--only", "beta_scatter")
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("theme_missing", r.stdout)                    # WARNING names the missing dir
            meta = self.read_meta(deck / "figs" / "slide", "beta_scatter")
            neutral = ENGINE / "themes" / "neutral"
            self.assertEqual(meta["stats"]["deck_theme"], str(neutral) if neutral.is_dir() else None)

    def test_no_config_defaults(self):
        with TempDeck(PLOT_DECK) as deck:
            (deck / "deck.config.js").unlink()
            r = run(PLOT, deck, "--only", "beta_scatter")
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            meta = self.read_meta(deck / "figures", "beta_scatter")
            # Same default as build.js: <deck>/theme when it exists (the fixture has one) ...
            self.assertEqual(meta["stats"]["deck_theme"], str((deck / "theme").resolve()))
            # ... and the engine's neutral theme when it does not.
            shutil.rmtree(deck / "theme")
            r = run(PLOT, deck, "--only", "beta_scatter")
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            meta = self.read_meta(deck / "figures", "beta_scatter")
            neutral = ENGINE / "themes" / "neutral"
            self.assertEqual(meta["stats"]["deck_theme"], str(neutral) if neutral.is_dir() else None)

    def test_fallback_savefig_without_style_save(self):
        with TempDeck(PLOT_DECK) as deck:
            style = deck / "plotting" / "style.py"
            style.write_text(style.read_text(encoding="utf-8").replace("def save(", "def _unused_save(")
                             .replace("DPI = THEME.get", "_DPI = THEME.get"), encoding="utf-8")
            r = run(PLOT, deck, "--only", "alpha_line")
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            png = (deck / "figures" / "alpha_line.png").read_bytes()    # theme.json dpi 40 -> 80 x 80
            self.assertEqual((int.from_bytes(png[16:20], "big"), int.from_bytes(png[20:24], "big")), (80, 80))

    def test_duplicate_names_exit_2(self):
        with TempDeck(PLOT_DECK) as deck:
            (deck / "plotting" / "c.py").write_text(
                "from plotting.b import beta_scatter\nFIGURES = {'alpha_line': beta_scatter}\n", encoding="utf-8")
            r = run(PLOT, deck, "--only", "beta_scatter")
            self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
            self.assertIn("'alpha_line' is registered by both plotting/a.py and plotting/c.py", r.stderr)
            self.assertFalse((deck / "figures").exists())

    def test_list_and_unknown(self):
        with TempDeck(PLOT_DECK) as deck:
            r = run(PLOT, deck, "--list")
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertEqual(r.stdout.splitlines(), ["alpha_bar\ta", "alpha_line\ta", "beta_scatter\tb"])
            self.assertFalse((deck / "figures").exists())
            r = run(PLOT, deck, "--only", "nope")
            self.assertEqual(r.returncode, 2)
            self.assertIn("unknown figure name(s): nope", r.stderr)

    def test_failing_figure_exit_1(self):
        with TempDeck(PLOT_DECK) as deck:
            (deck / "plotting" / "d.py").write_text(
                "def delta_bad():\n    return None\nFIGURES = {'delta_bad': delta_bad}\n", encoding="utf-8")
            r = run(PLOT, deck, "--only", "delta_bad")
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn("must return (figure, stats)", r.stderr)
            self.assertFalse((deck / "figures" / "run_meta" / "delta_bad.json").exists())


if __name__ == "__main__":
    unittest.main()
