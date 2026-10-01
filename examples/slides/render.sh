#!/usr/bin/env bash
# Build example decks, convert them to PDF (hidden supplementary slides included) and render preview PNGs.
#
#   bash examples/slides/render.sh                 # all decks: results narrative
#   bash examples/slides/render.sh results         # one deck
#
# Needs node + pptxgenjs (NODE_PATH or a local node_modules), LibreOffice (soffice) and pdftoppm.
# LibreOffice < 7.4 skips hidden slides when exporting PDF, so the PDF is made from a temp copy of the
# pptx without show="0"; the pptx in output/ keeps its supplementary slides hidden.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ $# -gt 0 ]; then DECKS=("$@"); else DECKS=(results narrative); fi
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
mkdir -p "$HERE/output" "$HERE/preview"

for deck in "${DECKS[@]}"; do
  builder="$HERE/build_${deck}.js"
  [ -f "$builder" ] || { echo "skip $deck: $builder not found"; continue; }
  node "$builder"
  pptx="$HERE/output/${deck}_examples.pptx"
  mkdir -p "$TMP/$deck/x"
  python3 - "$pptx" "$TMP/$deck/x/${deck}_examples.pptx" <<'EOF'
import sys, zipfile
src, dst = zipfile.ZipFile(sys.argv[1]), zipfile.ZipFile(sys.argv[2], "w", zipfile.ZIP_DEFLATED)
for item in src.infolist():
    data = src.read(item.filename)
    if item.filename.startswith("ppt/slides/slide") and item.filename.endswith(".xml"):
        data = data.replace(b' show="0"', b"")
    dst.writestr(item, data)
dst.close()
EOF
  soffice -env:UserInstallation="file://$TMP/lo_profile" --headless --convert-to pdf \
    --outdir "$TMP/$deck/x" "$TMP/$deck/x/${deck}_examples.pptx" >/dev/null 2>&1
  cp "$TMP/$deck/x/${deck}_examples.pdf" "$HERE/output/${deck}_examples.pdf"
  rm -f "$HERE/preview/${deck}"-*.png
  pdftoppm -r 60 -png "$HERE/output/${deck}_examples.pdf" "$HERE/preview/${deck}"
  echo "$pptx"
  echo "$HERE/output/${deck}_examples.pdf"
  ls "$HERE/preview/${deck}"-*.png
done
