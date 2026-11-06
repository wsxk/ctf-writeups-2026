#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
OUTPUT="$SCRIPT_DIR/SU_MusicPlayer.zip"

cat "$SCRIPT_DIR"/SU_MusicPlayer.zip.part-* > "$OUTPUT"

if [ -f "$SCRIPT_DIR/SU_MusicPlayer.zip.sha256" ]; then
  (cd "$SCRIPT_DIR" && shasum -a 256 -c SU_MusicPlayer.zip.sha256)
fi

echo "Restored: $OUTPUT"
