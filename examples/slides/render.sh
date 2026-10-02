#!/usr/bin/env bash
# Build the example decks with the results-deck engine and copy the page previews into preview/.
#
#   bash examples/slides/render.sh                 # all decks: results narrative
#   bash examples/slides/render.sh results         # one deck
#
# Each deck is a v2 deck directory examples/slides/<deck>/ (skills/results-deck/engine/SPEC.md). For each one
# this runs
#   node skills/results-deck/engine/js/build.js examples/slides/<deck> --out examples/slides/output/<deck>_examples.pptx --png
# which writes output/<deck>_examples.pptx (supplementary pages hidden), .pages.json, .pdf (every page, hidden
# ones included) and output/<deck>_examples_png/<NN>-<key>.png (60 dpi); the PNGs are then moved to
# preview/<deck>-NN.png. Needs node + pptxgenjs (NODE_PATH or a node_modules the engine finds), LibreOffice
# (soffice) and pdftoppm.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD="$HERE/../../skills/results-deck/engine/js/build.js"
if [ $# -gt 0 ]; then DECKS=("$@"); else DECKS=(results narrative); fi
mkdir -p "$HERE/output" "$HERE/preview"

for deck in "${DECKS[@]}"; do
  [ -f "$HERE/$deck/deck.config.js" ] || { echo "skip $deck: $HERE/$deck/deck.config.js not found"; continue; }
  node "$BUILD" "$HERE/$deck" --out "$HERE/output/${deck}_examples.pptx" --png
  png="$HERE/output/${deck}_examples_png"
  [ -d "$png" ] || { echo "ERROR: no PNGs in $png (see the WARNINGs above)" >&2; exit 1; }
  rm -f "$HERE/preview/${deck}"-*.png
  for f in "$png"/*.png; do
    b="$(basename "$f")"
    mv "$f" "$HERE/preview/${deck}-${b%%-*}.png"
  done
  rm -rf "$png"
  ls "$HERE/preview/${deck}"-*.png
done
