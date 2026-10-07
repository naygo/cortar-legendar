#!/usr/bin/env bash
# Une cortes (feitos com clip.sh) COM transições entre eles. Re-encoda (xfade), então só use quando houver transição.
# Uso: xjoin.sh <saida.mp4> --types "fadewhite,fade,corte" [--dur 0.3] <a.mp4> <b.mp4> [...]
#   --types: um tipo por junção, em ordem (repete se faltar). "corte" = sem transição.
#   Tipos úteis: fadewhite (luz/flash), fade (dissolver suave), fadeblack, dissolve, smoothleft...
# ponytail: "corte" vira um xfade de 1 frame (0.04s), não um corte literal; basta para o olho.
set -euo pipefail
OUT="${1:?uso: xjoin.sh <saida> --types a,b [--dur 0.3] <clips...>}"; shift
TYPES="fadewhite"; DUR=0.3
while [[ "${1:-}" == --* ]]; do
  case "$1" in --types) TYPES="$2"; shift 2 ;; --dur) DUR="$2"; shift 2 ;; *) echo "opção desconhecida: $1" >&2; exit 1 ;; esac
done
[[ $# -ge 2 ]] || { echo "precisa de 2+ clipes" >&2; exit 1; }
IFS=',' read -ra TY <<< "$TYPES"
N=$#; CLIPS=("$@")
INPUTS=(); for f in "${CLIPS[@]}"; do INPUTS+=(-i "$f"); done
FG=$(python3 - "$DUR" "$N" "${TY[*]}" "${CLIPS[@]}" <<'PY'
import sys, subprocess
dur=float(sys.argv[1]); n=int(sys.argv[2]); ty=sys.argv[3].split(); clips=sys.argv[4:]
d=[float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",c]).decode()) for c in clips]
v=a=None; acc=d[0]; parts=[]
for k in range(1,n):
    t=ty[(k-1)%len(ty)]
    td=0.04 if t=="corte" else dur
    t="fade" if t=="corte" else t
    off=acc-td
    vi=f"[{k}:v]"; ai=f"[{k}:a]"
    pv=f"[v{k-1}]" if k>1 else "[0:v]"; pa=f"[a{k-1}]" if k>1 else "[0:a]"
    parts.append(f"{pv}{vi}xfade=transition={t}:duration={td}:offset={off:.3f}[v{k}]")
    parts.append(f"{pa}{ai}acrossfade=d={td}[a{k}]")
    acc=acc+d[k]-td
print(";".join(parts))
PY
)
ffmpeg -hide_banner -loglevel warning -y "${INPUTS[@]}" -filter_complex "$FG" \
  -map "[v$((N-1))]" -map "[a$((N-1))]" \
  -c:v libx264 -preset medium -crf 20 -pix_fmt yuv420p -c:a aac -b:a 160k -ar 48000 -ac 2 -movflags +faststart "$OUT"
echo "OK: $OUT"
