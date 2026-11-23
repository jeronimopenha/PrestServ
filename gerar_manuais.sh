#!/usr/bin/env bash
set -euo pipefail

# Consolida os manuais em Markdown e, opcionalmente, gera os PDFs.
# Executar em qualquer diretório: bash docs/gerar_manuais.sh [--somente-md]

DIRETORIO="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIRETORIO"

if [[ "${1:-}" != "" && "${1:-}" != "--somente-md" ]]; then
    echo "Uso: bash gerar_manuais.sh [--somente-md]" >&2
    exit 2
fi

if ! command -v python3 >/dev/null 2>&1; then
    echo 'Erro: Python 3 não encontrado.' >&2
    exit 1
fi

# A versão consolidada é gerada automaticamente: não editar à mão.
python3 - <<'PY'
from pathlib import Path
import re

fontes = [
    ("Apresentação do PrestServ", "visao_geral.md"),
    ("Manual do porteiro", "manual_porteiro.md"),
    ("Manual da secretaria", "manual_secretaria.md"),
    ("Manual do perfil Consulta", "manual_consulta.md"),
    ("Manual do administrador", "manual_administrador.md"),
    ("Instalação e manutenção técnica", "instalacao_manutencao.md"),
]

partes = ["""---
title: "Manual completo do PrestServ"
subtitle: "Versão 2.0.0 - operação, administração e manutenção"
author: "Jeronimo Costa Penha"
date: "Novembro de 2026"
lang: pt-BR
---

"""]

for titulo, nome in fontes:
    texto = Path(nome).read_text(encoding="utf-8")
    texto = re.sub(r"\A---\s*\n.*?\n---\s*\n", "", texto, count=1, flags=re.S)
    partes.append(f"\\newpage\n\n# {titulo}\n\n{texto.strip()}\n\n")

Path("manual_completo.md").write_text("".join(partes), encoding="utf-8")
print("Consolidado: manual_completo.md")
PY

if [[ "${1:-}" == "--somente-md" ]]; then
    echo 'Finalizado: Markdown consolidado atualizado.'
    exit 0
fi

for comando in pandoc xelatex kpsewhich; do
    if ! command -v "$comando" >/dev/null 2>&1; then
        printf 'Erro: comando "%s" não encontrado.\n' "$comando" >&2
        exit 1
    fi
done

if [[ ! -f estilo_pdf.tex ]]; then
    echo 'Erro: estilo_pdf.tex não encontrado em docs/.' >&2
    exit 1
fi

if ! kpsewhich brazilian.ldf >/dev/null 2>&1; then
    echo 'Erro: suporte LaTeX ao português brasileiro não encontrado.' >&2
    echo 'No Arch: sudo pacman -S --needed texlive-langportuguese' >&2
    exit 1
fi

arquivos=(
    visao_geral.md
    manual_porteiro.md
    manual_secretaria.md
    manual_consulta.md
    manual_administrador.md
    instalacao_manutencao.md
    manual_completo.md
)

for entrada in "${arquivos[@]}"; do
    saida="${entrada%.md}.pdf"
    printf '\nGerando %s ...\n' "$saida"
    pandoc "$entrada" \
        --output "$saida" \
        --pdf-engine=xelatex \
        --toc --toc-depth=2 \
        --include-in-header=estilo_pdf.tex \
        --metadata=lang:pt-BR \
        -V papersize=a4 \
        -V mainfont='DejaVu Sans' \
        -V monofont='DejaVu Sans Mono' \
        -V geometry:margin=2.35cm \
        -V geometry:bottom=2.6cm
    printf 'Concluído: %s\n' "$saida"
done

printf '\nFinalizado: %d PDF(s) gerado(s).\n' "${#arquivos[@]}"
