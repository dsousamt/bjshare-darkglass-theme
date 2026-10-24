# BJ-Share DarkGlass (Zerfeus)

Tema para o BJ-Share, aplicado em **Configurações → Folha de estilo externa**.

Os arquivos são servidos direto deste repositório pelo GitHub Pages
(atualiza cerca de 1 minuto após cada push na `main`):

| Tema | URL |
| --- | --- |
| DarkGlass (base) | `https://dsousamt.github.io/bjshare-darkglass-theme/bj-zerfeus-theme.css` |
| Variantes | `https://dsousamt.github.io/bjshare-darkglass-theme/bj-zerfeus-theme-<nome>.css` |

Variantes: `light`, `dracula`, `sepia`, `highcontrast`, `oled`, `solarized`, `matrix`, `win95`, `monochrome`, `cyberpunk`.

Cada variante faz `@import` do base pela URL relativa (mesma pasta). Se o import
não carregar, use o bundle `bj-zerfeus-theme-<nome>.full.css` (base + variante num arquivo só).

Alternativa sem Pages: `https://cdn.jsdelivr.net/gh/dsousamt/bjshare-darkglass-theme@main/<arquivo>.css`
(o jsDelivr pode manter cache por até 12 h). Não use `raw.githubusercontent.com`: ele serve
os arquivos como `text/plain` e o navegador não aplica o CSS.

## Como o tema é organizado

`bj-zerfeus-theme.css` começa com dois blocos de variáveis:

- **1a. Sementes** — fundos, textos, acento, cores de estado, fontes e raios.
  É o que uma variante redefine.
- **1b. Derivados** — linhas, preenchimentos, rebaixos, sombras e tons do acento,
  calculados das sementes com `color-mix()`. Só redefina se o derivado não servir.

Três sementes controlam quase todos os tons sutis, e o alfa delas regula a intensidade:

- `--ink`: linhas finas e preenchimentos (branco em temas escuros, tinta escura em temas claros)
- `--recess`: áreas rebaixadas como cabeçalhos e campos (preto; branco translúcido em OLED)
- `--shade`: sombras (preto; azul-marinho com alfa baixo no tema claro)

## Criar uma variante

1. Copie `bj-zerfeus-theme-dracula.css` para `bj-zerfeus-theme-<nome>.css`.
2. Troque as sementes no `:root`.
3. Rode `.\build-theme-bundles.ps1`, que gera o `.full.css` de todas as variantes.
