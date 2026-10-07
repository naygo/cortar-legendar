# video-editor

Edição de vídeos de clientes (corte + legenda) com a skill `cortar-legendar` (`.claude/skills/`).

## Mapa

A empresa é uma pasta opcional: `clients/<empresa>/<cliente>/` (ex. `clients/acme/ana-souza/`) ou direto `clients/<cliente>/` (ex. `clients/bruno-lima/`). Abaixo, `clients/<cliente>/` vale para os dois.

```
clients/<cliente>/
├── brand/   logo, tag, finalização, paleta
├── raw/     vídeos originais
└── edit/
    └── editado_<nome-do-raw>/
        ├── final.mp4        resultado montado
        ├── cortes/          cortes separados (quando são a entrega)
        ├── imagens.md       ideias de imagem (se pedidas)
        └── _trabalho/       tudo que o Claude usa: transcrição, .ass, partes/, verify/, versoes/, project.md
```

## Convenções

- Cliente novo: criar `clients/<slug>/{brand,raw,edit}`.
- Saída de um raw `X.mp4` vai em `clients/<cliente>/edit/editado_X/` (só resultados na raiz; arquivos de trabalho em `_trabalho/`; nome do raw sem extensão; pode abreviar se for gigante, ex. `editado_roberta_0612`).
- Vai pro git: `.claude/`, `CLAUDE.md`, `README.md`, `LICENSE`, `.gitignore`. Não vai: nada em `clients/` (vídeos, transcrições, legendas, marca): é material de cliente, só local.
