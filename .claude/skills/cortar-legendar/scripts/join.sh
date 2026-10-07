#!/usr/bin/env bash
# Une cortes feitos com clip.sh (mesma resolução/codec) SEM re-encodar.
# Uso: join.sh <saida.mp4> <a.mp4> <b.mp4> [...]
set -euo pipefail
OUT="${1:?uso: join.sh <saida> <a.mp4> <b.mp4> ...}"; shift
[[ $# -ge 2 ]] || { echo "precisa de 2+ arquivos" >&2; exit 1; }
LIST="$(mktemp)"; trap 'rm -f "$LIST"' EXIT
for f in "$@"; do printf "file '%s'\n" "$(realpath "$f" | sed "s/'/'\\\\''/g")" >> "$LIST"; done
ffmpeg -hide_banner -loglevel warning -y -f concat -safe 0 -i "$LIST" -c copy -movflags +faststart "$OUT"
echo "OK: $OUT"
