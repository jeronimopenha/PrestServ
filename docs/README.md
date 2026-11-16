# Documentação do PrestServ — V1.1.0

**Desenvolvimento:** Jeronimo Costa Penha  
**Estado:** documentação da versão preparada para publicação; a instalação de produção pode permanecer na V1.0 até a implantação.

O PrestServ registra pessoas e atendimentos sociais. Esta pasta contém os documentos de operação, administração e manutenção.

| Arquivo | Público | Finalidade |
|:--|:--|:--|
| [visao_geral.md](visao_geral.md) | Todos | Objetivos, conceitos, perfis e funcionamento. |
| [manual_porteiro.md](manual_porteiro.md) | Porteiro | Registrar e corrigir atendimentos. |
| [manual_administrador.md](manual_administrador.md) | Administradores | Pessoas, usuários, relatórios, logs, backup e privacidade. |
| [instalacao_manutencao.md](instalacao_manutencao.md) | Responsável técnico | Instalação, SQLite, migração, testes e implantação. |
| [manual_completo.md](manual_completo.md) | Todos | Reunião dos quatro documentos acima. |

## Principais mudanças da V1.1.0

- Auditoria de acessos e operações, com consulta por filtros e visualização dos detalhes.
- Exclusão de logs selecionados, mediante confirmação e registro da limpeza.
- Exclusão de pessoas e usuários condicionada aos vínculos, com proteções administrativas.
- Migração automática para o esquema SQLite `user_version = 1`.
- Melhorias de apresentação dos relatórios PDF e compatibilidade dos componentes Streamlit.

O histórico de auditoria **não é imutável**: administradores autorizados podem remover registros. A restauração substitui o banco atual e pode perder alterações posteriores ao backup escolhido.

## Atualizar o manual completo e gerar os PDFs

O arquivo `manual_completo.md` é **gerado automaticamente** a partir dos manuais individuais por `gerar_manuais.sh`. Edite os manuais individuais primeiro e execute o script na pasta `docs/`:

```bash
bash gerar_manuais.sh
```

O script utiliza **Pandoc**, **XeLaTeX**, **Python 3**, o suporte a português brasileiro do TeX Live e `estilo_pdf.tex`. Gera os PDFs dos quatro manuais individuais e do manual completo, sempre com a autoria no rodapé.

Se desejar apenas regenerar `manual_completo.md`, execute o script com a opção `--somente-md`:

```bash
bash gerar_manuais.sh --somente-md
```

## Cuidados com a publicação

Não versionar o banco SQLite, backups, arquivos contendo dados pessoais ou segredos. Antes de atualizar a produção, fazer backup, validar a imagem Docker e revisar as instruções de manutenção.
