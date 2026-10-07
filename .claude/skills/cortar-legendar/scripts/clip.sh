#!/usr/bin/env bash
# Corta um trecho, opcionalmente reenquadra e queima legenda ASS — tudo numa passada só do ffmpeg.
# Uso:
#   clip.sh <entrada> <inicio> <fim> <saida.mp4> [--vertical | --res 1080x1350] [--subs legenda.ass] [--crf 20]
# Tempos: segundos (75.3) ou mm:ss(.ms) / hh:mm:ss(.ms)
# --vertical  = preenche 1080x1920 (9:16), cortando as laterais pelo centro
# --res WxH   = preenche essa resolução (ex.: 1080x1350 para 4:5, 1080x1080 quadrado)
# Sempre: 30fps, áudio 48kHz estéreo e fade de 30ms nas pontas (sem "estalo"); assim os cortes podem ser unidos com join.sh sem re-encodar.
set -euo pipefail

IN="${1:?uso: clip.sh <entrada> <inicio> <fim> <saida> [opções]}"
START="${2:?inicio}"; END="${3:?fim}"; OUT="${4:?saida}"; shift 4
RES=""; SUBS=""; CRF=20
while [[ $# -gt 0 ]]; do
  case "$1" in
    --vertical) RES="1080x1920" ;;
    --res) RES="$2"; shift ;;
    --subs) SUBS="$2"; shift ;;
    --crf) CRF="$2"; shift ;;
    *) echo "opção desconhecida: $1" >&2; exit 1 ;;
  esac
  shift
done

to_sec() { python3 -c 'import sys
t=0.0
for p in sys.argv[1].replace(",",".").split(":"): t=t*60+float(p)
print(t)' "$1"; }
S=$(to_sec "$START"); E=$(to_sec "$END")
DUR=$(python3 -c "print(max(0.0, $E - $S))")

FILTERS=("fps=30")
if [[ -n "$RES" ]]; then
  W="${RES%x*}"; H="${RES#*x}"
  FILTERS+=("scale=${W}:${H}:force_original_aspect_ratio=increase,crop=${W}:${H},setsar=1")
fi

IN_ABS="$(realpath "$IN")"
OUT_ABS="$(realpath -m "$OUT")"
mkdir -p "$(dirname "$OUT_ABS")"
WORKDIR="$(pwd)"
if [[ -n "$SUBS" ]]; then
  # roda no diretório da legenda para evitar problemas de escape de caminho no filtro ass
  WORKDIR="$(dirname "$(realpath "$SUBS")")"
  SUB_NAME="$(basename "$SUBS")"
  FILTERS+=("ass='${SUB_NAME//\'/\\\'}'")
fi

VF=()
if [[ ${#FILTERS[@]} -gt 0 ]]; then
  VF=(-vf "$(IFS=,; echo "${FILTERS[*]}")")
fi

cd "$WORKDIR"
ffmpeg -hide_banner -loglevel warning -stats -y \
  -ss "$S" -i "$IN_ABS" -t "$DUR" \
  "${VF[@]}" \
  -c:v libx264 -preset medium -crf "$CRF" -pix_fmt yuv420p \
  -af "afade=t=in:st=0:d=0.03,afade=t=out:st=$(python3 -c "print(max(0.0, $DUR - 0.03))"):d=0.03" \
  -c:a aac -b:a 160k -ar 48000 -ac 2 -movflags +faststart \
  "$OUT_ABS"

echo "OK: $OUT_ABS"
