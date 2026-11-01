#!/usr/bin/env bash
set -euo pipefail

# Gera os manuais do PrestServ com o mesmo estilo Pandoc + XeLaTeX.
# Coloque este arquivo em docs/, ao lado de estilo_pdf.tex.

DIRETORIO="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIRETORIO"

for comando in pandoc xelatex; do
    if ! command -v "$comando" >/dev/null 2>&1; then
        printf 'Erro: comando "%s" não encontrado.\n' "$comando" >&2
        exit 1
    fi
done

if [[ ! -f estilo_pdf.tex ]]; then
    echo 'Erro: arquivo docs/estilo_pdf.tex não encontrado.' >&2
    exit 1
fi

if ! kpsewhich brazilian.ldf >/dev/null 2>&1; then
    echo 'Erro: suporte ao português brasileiro ausente.' >&2
    echo 'No Arch: sudo pacman -S --needed texlive-langportuguese' >&2
    exit 1
fi

arquivos=(
    manual_completo.md
    manual_porteiro.md
    manual_administrador.md
    instalacao_manutencao.md
    visao_geral.md
)

quantidade=0
for entrada in "${arquivos[@]}"; do
    if [[ ! -f "$entrada" ]]; then
        printf 'Ignorando (não encontrado): %s\n' "$entrada"
        continue
    fi

    saida="${entrada%.md}.pdf"
    printf '\nGerando %s ...\n' "$saida"

    pandoc "$entrada" \
        --output "$saida" \
        --pdf-engine=xelatex \
        --toc \
        --toc-depth=2 \
        --include-in-header=estilo_pdf.tex \
        --metadata=lang:pt-BR \
        -V papersize=a4 \
        -V mainfont='DejaVu Sans' \
        -V monofont='DejaVu Sans Mono' \
        -V geometry:margin=2.35cm \
        -V geometry:bottom=2.6cm

    printf 'Concluído: %s\n' "$saida"
    quantidade=$((quantidade + 1))
done

printf '\nFinalizado: %d PDF(s) gerado(s).\n' "$quantidade"
