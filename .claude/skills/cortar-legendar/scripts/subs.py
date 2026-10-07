#!/usr/bin/env python3
"""Ferramentas de legenda para a skill cortar-legendar.

Subcomandos:
  show  <transcricao.json|.srt>                    Mostra a transcrição com timestamps (para escolher cortes)
  ass   <transcricao.json|.srt> --out legenda.ass   Gera legenda ASS estilizada para um trecho
        [--from 00:12.5] [--to 00:41]               Trecho do vídeo original (tempos já ficam relativos ao corte)
        [--res 1080x1920]                           Resolução do vídeo de saída
        [--words 3]                                 Palavras por legenda (só com JSON com timestamps por palavra)
        [--style reels|classico] [--font "Montserrat"] [--size N] [--color FFFFFF] [--pos 0.72]
        [--upper]                                   Texto em maiúsculas
  snap  <transcricao.json> --from INI --to FIM      Imprime "INI FIM" ajustados a limites de palavra (+folga 80/120ms)
"""
import argparse
import json
import re
import sys


# ---------- tempo ----------
def parse_time(s):
    """Aceita 75, 75.3, 1:15, 01:15.3, 0:01:15.3, 00:01:15,300."""
    if s is None:
        return None
    s = str(s).strip().replace(",", ".")
    parts = s.split(":")
    total = 0.0
    for p in parts:
        total = total * 60 + float(p)
    return total


def fmt_show(t):
    m, s = divmod(t, 60)
    h, m = divmod(int(m), 60)
    return f"{h}:{m:02d}:{s:04.1f}" if h else f"{m:02d}:{s:04.1f}"


def fmt_ass(t):
    t = max(0.0, t)
    cs = int(round(t * 100))
    h, cs = divmod(cs, 360000)
    m, cs = divmod(cs, 6000)
    s, cs = divmod(cs, 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


# ---------- leitura ----------
def load(path):
    """Retorna lista de segmentos: {start, end, text, words:[{start,end,word}]|None}."""
    if path.lower().endswith(".json"):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        segs = []
        for sg in data.get("segments", []):
            words = sg.get("words") or None
            if words:
                words = [{"start": float(w["start"]), "end": float(w["end"]),
                          "word": w["word"].strip()} for w in words if w.get("word", "").strip()]
            segs.append({"start": float(sg["start"]), "end": float(sg["end"]),
                         "text": sg["text"].strip(), "words": words})
        return segs
    # SRT
    with open(path, encoding="utf-8-sig") as f:
        blocks = re.split(r"\n\s*\n", f.read().strip())
    segs = []
    for b in blocks:
        lines = b.strip().splitlines()
        tl = next((i for i, l in enumerate(lines) if "-->" in l), None)
        if tl is None:
            continue
        a, z = [x.strip() for x in lines[tl].split("-->")]
        segs.append({"start": parse_time(a), "end": parse_time(z),
                     "text": " ".join(lines[tl + 1:]).strip(), "words": None})
    return segs


# ---------- show ----------
def cmd_show(args):
    for sg in load(args.input):
        print(f"[{fmt_show(sg['start'])} - {fmt_show(sg['end'])}] {sg['text']}")


# ---------- snap ----------
def cmd_snap(args):
    """Ajusta INI/FIM para limites de palavra + folga, sem invadir a palavra vizinha."""
    t0, t1 = parse_time(args.start), parse_time(args.end)
    ws = [w for sg in load(args.input) for w in (sg["words"] or [])]
    if not ws:
        sys.exit("erro: transcrição sem timestamps por palavra")
    i = next((k for k, w in enumerate(ws) if w["end"] > t0), None)
    j = next((k for k in range(len(ws) - 1, -1, -1) if ws[k]["start"] < t1), None)
    if i is None or j is None or j < i:
        sys.exit("erro: nenhuma palavra no intervalo")
    prev_end = ws[i - 1]["end"] if i > 0 else 0.0
    next_start = ws[j + 1]["start"] if j + 1 < len(ws) else ws[j]["end"] + args.pad_out
    ini = max(ws[i]["start"] - args.pad_in, (prev_end + ws[i]["start"]) / 2)
    fim = min(ws[j]["end"] + args.pad_out, (ws[j]["end"] + next_start) / 2)
    print(f"{ini:.2f} {fim:.2f}")


# ---------- ass ----------
STYLES = {
    # Fonte, tamanho relativo à altura, negrito, contorno relativo, sombra
    # padrão: branco, peso normal, SEM borda, sombra suave desfocada (referência do cliente), Montserrat
    # shadow = deslocamento da sombra; blur = desfoque dela (ambos relativos à altura)
    "reels":    {"size": 0.038, "bold": 0, "shadow": 0.0016, "blur": 0.004, "pos": 0.72},
    "classico": {"size": 0.032, "bold": 0, "shadow": 0.0016, "blur": 0.004, "pos": 0.92},
}


def split_fit(text, a, z, max_chars):
    """Sem timestamps por palavra: quebra o texto em pedaços que cabem numa linha, tempo proporcional aos caracteres."""
    parts, cur = [], ""
    for w in text.split():
        if cur and len(cur) + 1 + len(w) > max_chars:
            parts.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    if cur:
        parts.append(cur)
    total = sum(len(x) for x in parts) or 1
    out, t = [], a
    for x in parts:
        dt = (z - a) * len(x) / total
        out.append((t, t + dt, x))
        t += dt
    return out


def cues_from(segs, t0, t1, n_words, max_chars):
    """Gera (start, end, texto) já deslocados para começar em 0 no corte. Cada texto cabe em UMA linha."""
    cues = []
    for sg in segs:
        if sg["end"] <= t0 or (t1 is not None and sg["start"] >= t1):
            continue
        if sg["words"]:
            ws = [w for w in sg["words"] if w["end"] > t0 and (t1 is None or w["start"] < t1)]
            g = []
            for w in ws:
                cand = g + [w]
                too_many = n_words and len(cand) > n_words
                too_long = len(" ".join(x["word"] for x in cand)) > max_chars
                if g and (too_many or too_long):
                    cues.append((g[0]["start"], g[-1]["end"], " ".join(x["word"] for x in g)))
                    g = [w]
                else:
                    g = cand
            if g:
                cues.append((g[0]["start"], g[-1]["end"], " ".join(x["word"] for x in g)))
        else:
            cues += split_fit(sg["text"], sg["start"], sg["end"], max_chars)
    out = []
    for i, (a, z, txt) in enumerate(cues):
        # estende até a próxima legenda se o vão for pequeno (evita "piscar")
        if i + 1 < len(cues) and 0 < cues[i + 1][0] - z < 0.4:
            z = cues[i + 1][0]
        a = max(a, t0) - t0
        z = (min(z, t1) if t1 is not None else z) - t0
        if z - a > 0.05:
            out.append((a, z, txt))
    return out


def ass_escape(t):
    return t.replace("\\", "\\\\").replace("{", "(").replace("}", ")")


def cmd_ass(args):
    W, H = (int(x) for x in args.res.lower().split("x"))
    st = dict(STYLES[args.style])
    size = args.size or round(H * st["size"])
    shadow = max(1, round(H * st["shadow"]))
    blur = max(1, round(H * st["blur"]))
    pos = args.pos if args.pos is not None else st["pos"]
    margin_v = max(0, round(H * (1 - pos)))
    margin_h = round(W * 0.08)
    color = args.color.lstrip("#").upper()
    rr, gg, bb = color[0:2], color[2:4], color[4:6]
    primary = f"&H00{bb}{gg}{rr}"  # ASS usa BGR

    import shutil, subprocess
    if shutil.which("fc-list") and args.font.lower() not in subprocess.run(
            ["fc-list", ":", "family"], capture_output=True, text=True).stdout.lower():
        print(f"aviso: fonte '{args.font}' não instalada; o ffmpeg vai usar outra. Instale-a (ex. ~/.local/share/fonts/).", file=sys.stderr)

    t0 = parse_time(args.start) or 0.0
    t1 = parse_time(args.end)
    segs = load(args.input)
    has_words = any(s["words"] for s in segs)
    n_words = args.words if has_words else 0
    if args.words and not has_words:
        print("aviso: transcrição sem timestamps por palavra; dividindo por segmento (tempos proporcionais)", file=sys.stderr)

    # largura útil aproximada em caracteres: a legenda nunca quebra em 2 linhas, os eventos é que são divididos
    max_chars = max(8, int((W - 2 * margin_h) / (size * (0.72 if args.upper else 0.62))))

    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{args.font},{size},{primary},&H000000FF,&H00000000,&H00000000,{st['bold']},0,0,0,100,100,0,0,1,0,0,2,{margin_h},{margin_h},{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = []
    for a, z, txt in cues_from(segs, t0, t1, n_words, max_chars):
        if args.upper:
            txt = txt.upper()
        # camada 0: cópia preta desfocada deslocada (a sombra suave); camada 1: texto branco nítido
        px, py = W // 2, H - margin_v
        t = ass_escape(txt)
        lines.append(f"Dialogue: 0,{fmt_ass(a)},{fmt_ass(z)},Default,,0,0,0,,{{\\an2\\pos({px + shadow},{py + shadow})\\1c&H000000&\\1a&H70&\\blur{blur}}}{t}")
        lines.append(f"Dialogue: 1,{fmt_ass(a)},{fmt_ass(z)},Default,,0,0,0,,{{\\an2\\pos({px},{py})}}{t}")
    import os
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(header + "\n".join(lines) + "\n")
    print(f"OK: {args.out} ({len(lines) // 2} legendas)")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = p.add_subparsers(dest="cmd", required=True)
    s = sp.add_parser("show"); s.add_argument("input"); s.set_defaults(fn=cmd_show)
    a = sp.add_parser("ass")
    a.add_argument("input")
    a.add_argument("--out", required=True)
    a.add_argument("--from", dest="start")
    a.add_argument("--to", dest="end")
    a.add_argument("--res", default="1080x1920")
    a.add_argument("--words", type=int, default=3)
    a.add_argument("--style", choices=STYLES, default="reels")
    a.add_argument("--font", default="Montserrat")
    a.add_argument("--size", type=int)
    a.add_argument("--color", default="FFFFFF")
    a.add_argument("--pos", type=float, help="posição vertical da base da legenda (0=topo, 1=base)")
    a.add_argument("--upper", action="store_true")
    a.set_defaults(fn=cmd_ass)
    n = sp.add_parser("snap")
    n.add_argument("input")
    n.add_argument("--from", dest="start", required=True)
    n.add_argument("--to", dest="end", required=True)
    n.add_argument("--pad-in", type=float, default=0.08)
    n.add_argument("--pad-out", type=float, default=0.12)
    n.set_defaults(fn=cmd_snap)
    args = p.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
