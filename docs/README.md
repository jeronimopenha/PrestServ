# Documentação do PrestServ 2.0.0

**Desenvolvimento:** Jeronimo Costa Penha  
**Situação:** documentação da V2.0.0 candidata à publicação; a atualização da produção requer validação de migração e testes na infraestrutura real.

A documentação atende aos cinco perfis do PrestServ e ao responsável pela implantação e manutenção. O mapa técnico de arquivos foi atualizado após a reorganização em `security/`, `services/`, `scripts/` e `telas/`.

| Arquivo | Público | Conteúdo |
|:--|:--|:--|
| [visao_geral.md](visao_geral.md) | Todos | Conceitos, recursos, privacidade e perfis da V2. |
| [manual_porteiro.md](manual_porteiro.md) | Porteiro | Presenças de pessoas e voluntários na data atual. |
| [manual_secretaria.md](manual_secretaria.md) | Secretaria | Cadastros de pessoas e voluntários, entradas e situação cadastral. |
| [manual_consulta.md](manual_consulta.md) | Consulta | Relatórios e estatísticas agregadas, sem identificação de pessoas. |
| [manual_administrador.md](manual_administrador.md) | Admin e superadmin | Gestão operacional, relatórios, voluntários e recursos exclusivos do superadmin. |
| [instalacao_manutencao.md](instalacao_manutencao.md) | Responsável técnico | Instalação, permissões, backup, migração, Docker/Nginx e checklist de liberação. |
| [manual_completo.md](manual_completo.md) | Todos | Versão consolidada dos documentos acima, gerada pelo script. |

## Principais mudanças da V2.0.0

A V2 introduz cinco perfis, restrição de datas por função, quantidades de serviços, novos campos nos cadastros e controles relacionados a refeições no local, lançamento de entradas, módulo completo de voluntariado, estatísticas e certificados, além dos temas claro e escuro.

**Atenção aos limites:** os logs não são imutáveis, o SQLite não possui criptografia nativa no arquivo, os backups ZIP contêm dados sensíveis e as permissões do aplicativo não substituem os controles de acesso ao servidor.

## Consultar os manuais dentro do PrestServ

A V2.0.0 inclui a página **Documentação** dentro da aplicação, com visualização e download dos PDFs permitidos para cada perfil. O administrador técnico deve garantir que a pasta `docs/` (inclusive os PDFs) esteja disponível na implantação e que as permissões sejam verificadas também antes de ler cada arquivo.

## Gerar os manuais em PDF

Na pasta `docs/`, execute:

```bash
bash gerar_manuais.sh
```

O script recompõe `manual_completo.md` a partir dos manuais individuais e gera os PDFs com **Pandoc + XeLaTeX**, em escala de cinza e com a autoria no rodapé.

Para atualizar somente o Markdown consolidado:

```bash
bash gerar_manuais.sh --somente-md
```

O script requer Python 3. Para gerar PDFs, também são necessários Pandoc, XeLaTeX e o pacote LaTeX de português brasileiro. Os arquivos `.md` são as fontes editáveis; **não edite manualmente `manual_completo.md`**, pois ele é gerado.

## Procedimento para publicar

1. Revisar os manuais e os caminhos/configurações efetivamente usados na implantação.
2. Gerar backup validado da produção, copiar o banco para um ambiente isolado e realizar a migração controlada.
3. Confirmar integridade do banco migrado e executar o conjunto de testes da V2 em homologação.
4. Testar a imagem Docker, os volumes persistentes, o proxy Nginx e o login dos cinco perfis.
5. Somente após os testes, realizar atualização programada e, posteriormente, etiquetar/publicar a versão conforme o fluxo de entrega adotado.

A documentação não constitui prova de que a produção já tenha sido atualizada.
