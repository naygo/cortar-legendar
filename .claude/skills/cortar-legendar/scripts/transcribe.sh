#!/usr/bin/env bash
# Transcreve um vídeo com whisper-ctranslate2 (faster-whisper) e gera JSON com timestamps por palavra.
# Uso: transcribe.sh <video> [modelo=small] [idioma=pt] [pasta_saida=pasta do vídeo]
# Saída: <pasta_saida>/<nome_do_video>.json (e .srt/.txt/.vtt/.tsv de bônus). Use a pasta _trabalho/ do vídeo editado para não sujar raw/.
set -euo pipefail

VIDEO="${1:?uso: transcribe.sh <video> [modelo] [idioma]}"
MODEL="${2:-small}"
LANG_CODE="${3:-pt}"
OUT_DIR="${4:-$(dirname "$VIDEO")}"; mkdir -p "$OUT_DIR"

command -v whisper-ctranslate2 >/dev/null || {
  echo "whisper-ctranslate2 não encontrado. Instale com: pipx install whisper-ctranslate2" >&2; exit 1; }

BASE="$OUT_DIR/$(basename "${VIDEO%.*}")"
run() {
  whisper-ctranslate2 "$VIDEO" \
    --model "$MODEL" \
    --language "$LANG_CODE" \
    --word_timestamps True \
    --vad_filter True \
    --output_format all \
    --output_dir "$OUT_DIR" "$@"
}

# ponytail: tenta o device automático (GPU); se falhar (ex. sem libcublas) ou não gerar o .json, refaz em CPU
run || true
[ -s "${BASE}.json" ] || { echo "GPU/auto falhou, tentando CPU..." >&2; run --device cpu; }
[ -s "${BASE}.json" ] || { echo "ERRO: ${BASE}.json não foi gerado" >&2; exit 1; }
echo "OK: ${BASE}.json"
