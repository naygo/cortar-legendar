---
name: cortar-legendar
description: Corta trechos de vídeos e queima legendas estilizadas (estilo Reels/Shorts ou clássico) usando só ferramentas gratuitas e locais (ffmpeg + faster-whisper). Use quando pedirem para cortar, recortar, legendar, fazer Reels/Shorts/cortes de um vídeo, ou tirar silêncios.
---

# Cortar e legendar vídeos (100% local e gratuito)

Fluxo: **transcrever uma vez → escolher trechos lendo a transcrição → cortar + reenquadrar + legendar numa passada só**.

Scripts em `scripts/` (relativos a esta skill):
- `transcribe.sh <video> [modelo=small] [idioma=pt] [pasta_saida]` → gera `<nome>.json` (timestamps por palavra) e `.srt` na `pasta_saida` (use `_trabalho/`)
- `subs.py show <video.json>` → transcrição compacta com tempos, para escolher cortes
- `subs.py ass <video.json> --from INI --to FIM --out clipe.ass [--res 1080x1920] [--words 3] [--style reels|classico] [--upper] [--font "..."] [--color FFFFFF] [--pos 0.72]`
- `subs.py snap <video.json> --from INI --to FIM` → imprime `INI FIM` ajustados a limites de palavra + folga (nunca corta no meio de palavra)
- `xjoin.sh <saida.mp4> --types "fadewhite,fade" [--dur 0.3] <a.mp4> <b.mp4> ...` → une cortes COM transições (re-encoda); `corte` num tipo = sem transição naquela junção
- `join.sh <saida.mp4> <a.mp4> <b.mp4> ...` → une cortes feitos pelo `clip.sh` sem re-encodar
- `clip.sh <video> INI FIM <saida.mp4> [--vertical | --res WxH] [--subs clipe.ass] [--crf 20]`

## Briefing (perguntar ANTES de tudo)

Regras para perguntar:
- **Linguagem do dia a dia.** A pessoa edita vídeo, não é técnica: nada de flags, `punch-in`, `CTA`, `motion graphics` sem explicar. Descreva o resultado ("o vídeo dá uma aproximada rápida quando você fala algo importante").
- **Use AskUserQuestion, no máximo 4 perguntas por vez, cada uma com 2-4 opções clicáveis**, a recomendada primeiro, com uma frase curta dizendo o que muda. Nunca pergunta aberta quando dá para oferecer opções.
- **Pule o que o pedido já respondeu** ou o que dá para descobrir sozinho (ex.: logo/tag/finalização já estão em `clients/<cliente>/brand/`; olhe lá antes de perguntar). Registre as respostas e use-as nos passos abaixo.

**Rodada 1, sempre** (uma chamada, 4 perguntas; a 1b vem depois):

| Pergunta (como falar) | Opções | O que muda |
|---|---|---|
| "Qual resultado você espera receber?" | **Um vídeo só**, montado com os melhores trechos (ex.: 1 vídeo de ~60-90s) / **Vários vídeos curtos separados** (ex.: 3 Reels de até 60s cada) / **O vídeo inteiro**, só limpo e legendado (sem tirar conteúdo) / Eu escolho os trechos | Saída: um vídeo só → `final.mp4`; vários curtos → `cortes/01.mp4, 02.mp4...`; inteiro → `final.mp4` com a duração original. **Transições só se aplicam a "um vídeo só"** (entre vários vídeos separados não existe junção) |
| "Onde o vídeo vai ser postado?" | Reels/TikTok/Shorts (vertical) / Feed do Instagram (4:5) / YouTube (horizontal) | `--res` 1080x1920 / 1080x1350 / 1920x1080 |
| "Quer transições entre os cortes?" | Sim, de luz alternando com dissolver suave (recomendado) / Só de luz / Corte seco, sem transição / Outro estilo (descrever) | Passo 5: `xjoin.sh`, **só quando o resultado é "um vídeo só"** (senão pule e não pergunte). Padrão = luz (`fadewhite`) alternada com dissolver (`fade`), ver regras abaixo |
| "Qual a vibe do vídeo e do cliente?" | Médica/séria e confiável / Nutrição/leve e acolhedora / Outra (descrever) | Só o **tom**: escolha dos trechos, gancho e linguagem das sugestões. **Não muda a legenda**, que é sempre branca básica por padrão (ver Rodada 2) |

**Pergunta 1b, logo em seguida, só se a resposta for "um vídeo só" ou "vários vídeos"** (outra chamada curta, com opções de clique): "Quanto tempo?" → para um vídeo só: ~30s / ~60s (recomendado) / ~90s / mais longo; para vários: quantos (2 / 3 recomendado / 5) e duração de cada (até 30s / até 60s recomendado). Não adivinhe número nem duração.

**Regras das transições** (sem exagero): só nas **trocas de ideia** (gancho → conteúdo → chamada final); cortes dentro da mesma ideia ficam secos. No máximo **2 tipos** no vídeo, alternando em ordem (luz, dissolver, luz...), nunca o mesmo tipo duas vezes seguidas se houver 2 tipos, curtas (0,25-0,4s). Se a pessoa pedir outro estilo, use outro tipo do `xfade` do ffmpeg (`fadeblack`, `dissolve`, `smoothleft`...) mantendo a mesma lógica.

**Rodada 2, só se o pedido não disser** (uma chamada, 4 perguntas):

| Pergunta | Opções | O que muda |
|---|---|---|
| "Quer uma legenda diferente da padrão (branca, simples)?" | Não, manter a padrão (recomendado) / Sim, quero outro estilo (perguntar qual: cor, tamanho, frase completa em vez de palavra por palavra) | Padrão: branca, **Montserrat** peso normal (não negrito), sem borda, só sombra suave desfocada, uma linha só (referência do cliente: texto branco fino com sombra difusa) (`--style reels --color FFFFFF`, sem `--font` nem `--upper`; Poppins é a alternativa: `--font Poppins`). Só mude se a pessoa pedir: `--style classico --words 0`, `--color`, `--font`, `--upper` |
| "Quer zoom no vídeo?" | Não / Aproximadas rápidas quando falar algo importante / Zoom lento e contínuo | Aplique com ffmpeg (`zoompan` ou `crop`+`scale`) depois do corte e **antes** da legenda, senão o zoom estica o texto. O `clip.sh` não faz isso sozinho |
| "Quer ideias de imagens para ilustrar o vídeo?" | Não / Sim, uma lista | Tabela em `imagens.md`: tempo, o que a pessoa fala (trecho), imagem sugerida. Máx. 1 linha por ideia, sem jargão |
| "Quer animações na tela (títulos, ícones, setas)?" | Não / Sim | Se sim, siga com as skills `hyperframes:*`; esta skill só entrega corte + legenda |

**Rodada 3, só se fizer sentido** (texto livre, curta, uma pergunta por linha): tirar pausas e vícios de fala ("né", "tipo") → passo 2 (`auto-editor`); algo no final do vídeo além da finalização do cliente (ex. "chame para agendar consulta"); nomes/marcas/termos que costumam sair errados na transcrição (corrija no `.json` antes do `.ass`); idioma da fala (padrão pt; tradução exige passo extra).

Não pergunte: tom/público (deduza da transcrição) nem se há pessoa na tela (olhe um frame, passo 1).

## Pastas (convenção do repositório)

Veja `CLAUDE.md` na raiz. Resumo: `clients/<cliente>/{brand,raw,edit}`, onde `<cliente>` pode estar dentro de uma pasta de empresa (`clients/<empresa>/<cliente>/`). Descubra o caminho pelo vídeo de origem (a pasta que contém `raw/`).
- Origem: vídeo em `clients/<cliente>/raw/`. Marca (logo, tag, finalização) em `brand/`: use-a em vez de perguntar o caminho (não precisa perguntar).
- Saída: `clients/<cliente>/edit/editado_<nome-do-raw>/` deve conter **só o que é resultado**, para a pessoa abrir e ver na hora:
  - `final.mp4`: o vídeo único montado (se foi pedido);
  - `cortes/`: os vídeos curtos separados **quando "vários vídeos" é a entrega** (ex. 3 Reels de até 60s): só os `.mp4` finais;
  - `imagens.md`: ideias de imagem, se pedidas;
  - `_trabalho/`: **tudo o que você usa para fazer** (o `_` faz a pasta ficar no topo, fora do caminho): transcrição (`.json/.srt/.txt/.vtt/.tsv`), legendas `.ass`, `partes/` (trechos que só servem para montar o `final.mp4`), `verify/` (frames de conferência), versões antigas/intermediárias (`versoes/`) e `project.md`.
- Nunca deixe arquivos soltos em `raw/` nem arquivos de trabalho na raiz de `editado_*/`. Para a transcrição: `scripts/transcribe.sh VIDEO small pt "$W"   # W = .../editado_<nome>/_trabalho "$W"`, com `W=clients/<cliente>/edit/editado_<nome>/_trabalho`.
- Se o cliente não tiver pasta, pergunte o nome e crie `clients/<slug>/{brand,raw,edit}`.

## 0. Pré-requisitos

Confira antes de começar: `command -v ffmpeg whisper-ctranslate2`. Se faltar algo, peça à pessoa para instalar (não instale com sudo por conta própria):
- Debian/Ubuntu: `sudo apt install ffmpeg pipx && pipx ensurepath && pipx install whisper-ctranslate2`
- Opcional, para tirar silêncios: `pipx install auto-editor`

## 1. Inspecionar o vídeo

```bash
ffprobe -v error -show_entries stream=codec_type,width,height:stream_side_data=rotation -show_entries format=duration -of compact VIDEO
```
Atenção: vídeos de celular costumam ter **rotação nos metadados** (ffprobe mostra 1920x1080, mas o vídeo é vertical). O ffmpeg aplica a rotação automaticamente. Em caso de dúvida, extraia um frame e olhe:
`ffmpeg -ss 5 -i VIDEO -frames:v 1 -vf scale=480:-1 frame.png`

## 2. (Opcional) Tirar silêncios

Só se pedirem, ou se o vídeo for fala corrida com muitas pausas:
```bash
auto-editor VIDEO --margin 0.2s -o VIDEO_limpo.mp4
```
Depois use `VIDEO_limpo.mp4` nos passos seguintes.

## 3. Transcrever (uma vez por vídeo)

```bash
scripts/transcribe.sh VIDEO small pt "$W"   # W = .../editado_<nome>/_trabalho
```
- Modelos: `base` (rápido, máquina fraca), `small` (padrão), `medium` (melhor qualidade, bem mais lento em CPU).
- Se o `.json` já existir em `_trabalho/` (ou ao lado do vídeo, em trabalhos antigos), reaproveite e não transcreva de novo.
- O script tenta GPU e cai para CPU sozinho; só diz "OK" se o `.json` existir. Se der erro, mostre-o à pessoa em vez de seguir.

## 4. Escolher os cortes e CONFIRMAR O PLANO

```bash
scripts/subs.py show "$W"/<nome>.json
```
Leia a transcrição e escolha trechos de acordo com o pedido. Boas práticas:
- Para Reels/Shorts: gancho forte nos primeiros 3s; duração entre 15 e 60s, salvo pedido diferente.
- **Gravação com várias tentativas (takes):** é comum em gravações do Riverside. Procure frases repetidas ou recomeços na transcrição, monte a ordem pelas **ideias** (gancho → conteúdo → chamada final), não pela ordem do arquivo, e para cada ideia escolha o take mais limpo (sem tropeço, sem recomeço). Se só existir take com deslize, use-o e avise.
- Prefira cortar em pausas ≥ 0,4s; pausa < 0,15s é meio de frase (inseguro).
- Confira os extremos de cada trecho com `scripts/subs.py snap "$W"/<nome>.json --from INI --to FIM`: ele devolve `INI FIM` em limite de palavra com folga de 80/120ms. Use esses valores no passo 5.

**Sempre confirme o plano antes de renderizar** (renderizar um vídeo grande à toa é caro). Mostre em português simples, sem tempos técnicos demais:
- ordem dos cortes, com o que cada um diz (1 linha) e duração;
- qual take foi escolhido e por quê, se houve takes repetidos;
- duração total, formato, legenda (padrão ou a escolhida), transições (quais e em que junções), finalização/logo;
- o que ficou de fora (trechos descartados) em uma linha.

Só renderize depois do ok. Repita no plano, em palavras simples, **qual resultado entendeu** ("vou entregar 3 vídeos separados de até 60s" ou "1 vídeo único de ~60s com 4 trechos") para a pessoa corrigir antes de renderizar. Se a pessoa já deu um plano exato ("corta de 1:20 a 2:05"), apenas repita-o em uma linha e siga.

## 5. Gerar legenda e renderizar cada corte

Para cada trecho, use os **mesmos INI/FIM** nos dois comandos (a legenda já sai com tempo relativo ao corte):
```bash
read INI FIM < <(scripts/subs.py snap "$W"/<nome>.json --from 1:20.3 --to 2:05)   # limites de palavra (snap lê "$W"/<nome>.json)
scripts/subs.py ass "$W"/<nome>.json --from $INI --to $FIM --out "$W"/legendas/01.ass --res 1080x1920 --words 3 --upper
scripts/clip.sh VIDEO $INI $FIM cortes/01.mp4 --vertical --subs "$W"/legendas/01.ass
```
Onde gravar o `.mp4`: `cortes/01.mp4` se o corte é a **entrega** separada; `"$W"/partes/01.mp4` se só serve para montar o `final.mp4` (nesse caso o `join.sh`/`xjoin.sh` gera `final.mp4` na raiz de `editado_*/`; os exemplos abaixo usam `cortes/` só como ilustração).

O `clip.sh` já aplica fade de áudio de 30ms nas pontas, 30fps e áudio 48kHz estéreo. Por isso os cortes podem ser unidos **sem re-encodar** (`scripts/join.sh final.mp4 cortes/01.mp4 cortes/02.mp4 ...`) quando não há transição, ou **com transições** via `scripts/xjoin.sh final.mp4 --types "fadewhite,fade,corte" cortes/01.mp4 cortes/02.mp4 cortes/03.mp4` (um tipo por junção, na ordem; use `corte` onde a ideia não muda, conforme as regras da Rodada 1). Para anexar a finalização, passe-a antes pelo `clip.sh` (com o mesmo `--vertical`/`--res`) para ficar com os mesmos parâmetros, e então junte. Ordem dos filtros: reenquadrar/zoom → **legenda por último** (senão o zoom estica o texto).
- `--res` do `subs.py` deve ser a resolução final do vídeo: `1080x1920` com `--vertical`, a mesma do `--res` do clip.sh, ou a resolução original (já considerando rotação) se não houver reenquadramento.
- Estilos: `reels` (grande, ~72% da altura, até 3 palavras por vez) ou `classico` (menor, rodapé, `--words 0` = frases). Em ambos: **sem borda, só sombra desfocada** (camada preta com blur atrás do texto), e **sempre uma linha só**: o `subs.py` nunca quebra linha, ele divide a fala em mais eventos quando não cabe (em 1080 de largura cabem ~14-17 caracteres no `reels`).
- Outros formatos: feed 4:5 → `--res 1080x1350` em ambos; quadrado → `1080x1080`.
- Sem legenda: omita o `--subs`.

### Marca do cliente (`clients/<cliente>/brand/`)

Se existir `brand/`, use por padrão, sem perguntar: **finalização** (`finalizacao*.mp4`) anexada no fim de cada corte (concat com ffmpeg, reescalando para a mesma resolução e com áudio compatível) e **logo/tag** quando fizer sentido no layout. Se for pular algo, diga na entrega ("não usei a finalização porque X"), nunca em silêncio.

## 6. Conferir (antes de mostrar à pessoa)

No arquivo **final** (não nas fontes):
```bash
ffprobe -v error -show_entries stream=width,height -show_entries format=duration -of csv=p=0 final.mp4
ffmpeg -i final.mp4 -af ebur128=peak=true -f null - 2>&1 | tail -12   # loudness e pico
ffmpeg -ss T -i final.mp4 -frames:v 1 -vf scale=360:-1 "$W"/verify/T.png   # um frame por ponto abaixo
```
Olhe (com a ferramenta de ler imagem) frames em: **cada ponto de corte (±1s)**, os primeiros 2s, os últimos 2s e 2-3 pontos no meio. Procure:
- salto/flash visual no corte; legenda cobrindo o rosto ou saindo da tela (ajuste `--pos`: 0.80 desce, 0.60 sobe);
- finalização/logo no lugar certo e áudio sem queda brusca de volume entre os trechos;
- duração bate com o plano; loudness razoável (em torno de -14 a -16 LUFS integrado; pico ≤ -1 dBTP). Você não consegue ouvir o áudio: diga isso e informe só os números.

Se algo falhar: corrija → renderize de novo → confira de novo. **No máximo 3 rodadas**; se ainda houver problema, relate à pessoa em vez de repetir. Para ver o vídeo inteiro com mais detalhe, pode-se usar a skill `watch` com `--engine local` (o motor Gemini envia o vídeo ao Google: não use em vídeo de cliente).

Revise também a transcrição nos trechos escolhidos: nomes próprios e termos técnicos costumam sair errados. **Não corrija por palpite.** Liste à pessoa cada correção proposta ("dozo" → "doze", "Quadrão" → "Padrão"...) e peça confirmação antes de editar o `.json` (campo `word`). Correção que depende de adivinhar a frase inteira (ex. uma frase que saiu truncada) só com ok explícito; na dúvida, mantenha o que foi falado e pergunte.

## Memória do vídeo

Ao terminar, crie/atualize `project.md` em `_trabalho/` (dentro de `editado_<nome-do-raw>/`) (acrescente uma seção por sessão): estratégia em 1 parágrafo, decisões (takes escolhidos, o que foi cortado e por quê), respostas do briefing e pendências. Ao retomar um vídeo, leia esse arquivo primeiro e resuma a última sessão em uma frase.

## Entrega

Diga onde estão os arquivos (em `clients/<cliente>/edit/editado_<nome-do-raw>/`, só `final.mp4`, `cortes/` e `imagens.md`; o resto fica em `_trabalho/`), a duração de cada corte e um resumo de uma linha do conteúdo de cada um.
