# cortar-legendar

Skill do Claude Code para edição de vídeos de clientes: corta os melhores trechos de uma gravação e queima legenda, tudo local e gratuito (ffmpeg + faster-whisper). A automação é a skill `cortar-legendar`, em `.claude/skills/`.

## Como funciona

1. Você coloca o vídeo original em `clients/<cliente>/raw/`.
2. Chama `/cortar-legendar` no Claude Code.
3. O Claude faz algumas perguntas rápidas (formato, quantidade de cortes, vibe, legenda...).
   Depois mostra o **plano** (ordem dos cortes, takes escolhidos, duração) e só renderiza com o seu ok.
4. Transcreve o vídeo uma vez (Whisper, com tempo por palavra) e escolhe os trechos lendo a transcrição.
5. Corta, reenquadra (ex. vertical 1080x1920), queima a legenda e anexa a finalização do cliente.
6. Confere o resultado (frames nos cortes, volume, duração) e entrega tudo em `clients/<cliente>/edit/editado_<nome-do-raw>/`.

## Começando

```bash
git clone https://github.com/naygo/cortar-legendar.git
cd cortar-legendar
claude          # abra o Claude Code na raiz: a skill do projeto é carregada
```

Para usar a skill em **qualquer** pasta, copie `.claude/skills/cortar-legendar/` para `~/.claude/skills/` (e não deixe a cópia do projeto ao mesmo tempo, ou ela aparece duas vezes na lista).

## Instalação

Precisa de Linux/macOS, [Claude Code](https://claude.com/claude-code) e:

```bash
# Debian/Ubuntu
sudo apt install ffmpeg pipx
pipx ensurepath
pipx install whisper-ctranslate2     # transcrição (faster-whisper)
pipx install auto-editor             # opcional: tirar silêncios
```

- Sem GPU tudo funciona em CPU; o script de transcrição cai para CPU sozinho se a GPU falhar.
- O primeiro uso baixa o modelo do Whisper (`small` por padrão), então precisa de internet uma vez.
- Confira: `command -v ffmpeg whisper-ctranslate2`.

Depois de clonar, abra o Claude Code **na raiz do repositório** para a skill do projeto ser carregada. Se `/cortar-legendar` aparecer duas vezes na lista, existe uma cópia antiga em `~/.claude/skills/`; apague-a.

## Como usar

```
/cortar-legendar @0711
```

Digite `@` + parte do nome para escolher o vídeo no autocompletar (ou cole o caminho). A skill pergunta, em até 3 rodadas:

| Rodada | Quando | O quê |
|---|---|---|
| 1 | sempre | o resultado esperado (um vídeo só, vários curtos ou o vídeo inteiro; depois quantos e quanto tempo), onde vai postar, transições (padrão: luz alternando com dissolver), vibe do cliente |
| 2 | se o pedido não disser | legenda diferente da padrão, zoom, ideias de imagem, animações |
| 3 | só se fizer sentido | tirar pausas e vícios de fala, final do vídeo, termos que a transcrição erra, idioma |

Padrões: legenda **branca simples**, palavra por palavra (estilo Reels). A skill pede confirmação antes de corrigir a transcrição e antes de renderizar, se o pedido for vago.

## Estrutura

A pasta da empresa é opcional: `clients/<empresa>/<cliente>/` ou `clients/<cliente>/`.

```
clients/<cliente>/
├── brand/   logo, tag, finalização do cliente
├── raw/     vídeos originais
└── edit/
    └── editado_<nome-do-raw>/
        ├── final.mp4   cortes/   imagens.md      ← só os resultados
        └── _trabalho/                            ← transcrição, legendas .ass, partes, versões, project.md
.claude/skills/cortar-legendar/  a skill: SKILL.md + scripts/
CLAUDE.md                        mapa e convenções para o Claude
```

Cliente novo: crie `clients/<slug>/{brand,raw,edit}` e ponha logo, tag e finalização em `brand/`.

## O que vai pro git

Este repositório versiona só a skill e a documentação. Tudo em `clients/` (vídeos, transcrições, legendas **e a marca dos clientes**) é ignorado pelo `.gitignore` e fica só na sua máquina. Se quiser versionar a marca dos seus clientes, faça-o num repositório **privado**.

## Scripts da skill

Em `.claude/skills/cortar-legendar/scripts/`, normalmente chamados pelo Claude:

- `transcribe.sh <video> [modelo] [idioma]`: gera `.json` com tempo por palavra (e `.srt`). Modelos: `base`, `small` (padrão), `medium`.
- `subs.py show <video.json>`: transcrição compacta com tempos. `subs.py ass ...` gera a legenda `.ass` de um trecho.
- `subs.py snap <video.json> --from INI --to FIM`: ajusta os extremos a limites de palavra (nunca corta no meio de uma palavra).
- `xjoin.sh <saida.mp4> --types "fadewhite,fade" <a.mp4> <b.mp4>...`: une cortes com transições (luz, dissolver...).
- `join.sh <saida.mp4> <a.mp4> <b.mp4>...`: une cortes sem re-encodar.
- `clip.sh <video> INI FIM <saida.mp4> [--vertical | --res WxH] [--subs x.ass]`: corta, reenquadra e queima a legenda (30fps, fade de áudio de 30ms nas pontas).

## Fonte da legenda

O padrão é **Montserrat** (peso normal, branca, sombra suave). Instale-a (Google Fonts) em `~/.local/share/fonts/` e rode `fc-cache -f`; Poppins também funciona (`--font Poppins`). Sem a fonte, o ffmpeg usa outra e o `subs.py` avisa.

## Limites

- Zoom in/out e anexar finalização/logo são feitos pelo Claude com ffmpeg em cada vídeo; não são flags dos scripts.
- Animações na tela (títulos, ícones) ficam com as skills `hyperframes:*`, não com esta.
- A transcrição erra nomes e termos técnicos; revise as correções que a skill propuser.

## Licença

[MIT](LICENSE)
