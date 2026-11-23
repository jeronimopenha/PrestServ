# PrestServ

Sistema web de apoio ao registro de atendimentos sociais, à organização de pessoas atendidas e voluntários e ao acompanhamento de serviços, entradas e resultados.

**Versão em preparação:** 2.0.0  
**Versão em produção:** verificar a instalação institucional antes de atualizar.  
**Desenvolvimento:** Jeronimo Costa Penha.

## O que a versão 2.0.0 oferece

- Registro de presenças por pessoa e data, com serviços e quantidades.
- Cadastro de pessoas atendidas, fotos, contatos, endereço, observações e situação ativa/inativa.
- Controle de entradas, incluindo doações e compras.
- Cadastro e presença diária de voluntários, estatísticas, relatórios e certificados.
- Cinco perfis de acesso: superadministrador, administrador, secretaria, porteiro e consulta.
- Relatórios, exportações CSV/PDF, registros de auditoria e cópias ZIP do banco.
- Interface com temas claro e escuro, usando a configuração nativa do Streamlit.

O detalhamento dos acessos consta na [visão geral](docs/visao_geral.md) e nos [manuais](docs/README.md).

## Instalação, documentação e publicação

Acesse [docs/README.md](docs/README.md) para os manuais operacionais, a documentação técnica e a geração dos PDFs.

**Importante:** a V2.0.0 ainda depende da validação final de migração e implantação. Não utilize uma cópia de banco V1 diretamente com a aplicação V2 sem realizar o procedimento de migração controlada documentado.

O banco SQLite, fotografias, backups, segredos e arquivos com dados pessoais não devem ser publicados no Git.

## Histórico de versões

- **V1.0:** primeira publicação institucional.
- **V1.1.0:** ciclo de evolução de auditoria, exclusões condicionadas e documentação; confirme se foi implantada no ambiente em uso.
- **V2.0.0:** versão em preparação, com novos perfis, quantidades, entradas, voluntários, melhorias operacionais, relatórios e temas.

**Desenvolvido por Jeronimo Costa Penha.**
