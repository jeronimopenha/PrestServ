# Documentação do PrestServ 1.0

**Desenvolvimento:** Jeronimo Costa Penha

O PrestServ registra pessoas atendidas e serviços prestados por uma instituição de assistência social. Esta pasta contém a documentação de operação e manutenção.

| Arquivo | Público | Finalidade |
|:--|:--|:--|
| [visao_geral.md](visao_geral.md) | Todos | Objetivos, conceitos e funcionamento. |
| [manual_porteiro.md](manual_porteiro.md) | Operadores de atendimento | Registrar, consultar e corrigir atendimentos. |
| [manual_administrador.md](manual_administrador.md) | Administradores | Cadastros, usuários, relatórios, backups e privacidade. |
| [instalacao_manutencao.md](instalacao_manutencao.md) | Responsável técnico | Instalação, inicialização do banco e manutenção. |

## Publicação

Os arquivos Markdown são a fonte editável da documentação e podem ser mantidos no GitHub. Os PDFs de distribuição podem ser regenerados sempre que o conteúdo mudar. Os PDFs preparados nesta entrega incluem o nome do desenvolvedor no rodapé das páginas.

**Nota de revisão:** os procedimentos de backup/restauração e a configuração de implantação devem ser testados na versão final efetivamente instalada antes de entregar o sistema a usuários reais. A documentação não substitui esses testes.

## Regenerar o PDF com rodapé de autoria

Com Pandoc e XeLaTeX instalados, dentro da pasta da documentação:

```bash
pandoc manual_completo.md -o manual_completo.pdf \
  --pdf-engine=xelatex --toc --toc-depth=2 \
  -H estilo_pdf.tex \
  -V lang=pt-BR -V papersize=a4 \
  -V mainfont='DejaVu Sans' \
  -V monofont='DejaVu Sans Mono' \
  -V geometry:margin=2.35cm \
  -V geometry:bottom=2.6cm
```

O arquivo `estilo_pdf.tex` define o cabeçalho em tons de cinza e o rodapé com os créditos **Desenvolvido por Jeronimo Costa Penha** e a paginação. `manual_completo.md` reúne o conteúdo dos manuais separados; ao alterá-los, atualize também o consolidado antes da próxima exportação.
