---
title: "Instalação e manutenção técnica"
subtitle: "PrestServ 2.0.0 - configuração, migração e publicação"
author: "Jeronimo Costa Penha"
date: "Novembro de 2026"
lang: pt-BR
---

## 1. Arquitetura e estado da versão

O PrestServ utiliza **Python**, **Streamlit**, **SQLite**, **Pillow**, **pandas** e **ReportLab**. A implantação institucional conhecida usa **Docker** para executar a aplicação e **Nginx** como proxy reverso, com persistência do banco por volume ou montagem do diretório de dados.

A **V2.0.0 é candidata à publicação**. A documentação não confirma que o contêiner, o Nginx ou o banco de produção já tenham sido atualizados. Não inicie a V2 sobre um banco antigo sem executar e validar a migração.

## 2. Componentes do projeto

Arquivos principais (lista de referência, não necessariamente exaustiva):

```text
PrestServ/
├── app.py
├── auth.py
├── backup.py
├── cadastros.py
├── common.py
├── consultas_relatorios.py
├── consultas_voluntarios.py
├── criar_admin.py
├── database.py
├── estrutura_v110.py
├── estrutura_v200.py
├── estrutura_voluntarios.py
├── fotos.py
├── inicializar_banco.py
├── pdf_relatorios.py
├── pdf_voluntarios.py
├── certificados_voluntarios.py
├── permissoes.py
├── presencas.py
├── relatorios.py
├── tela_backups.py
├── tela_logs.py
├── tela_cadastros_voluntarios.py
├── tela_presencas_voluntarios.py
├── tela_relatorios_voluntarios.py
├── voluntarios.py
├── requirements.txt
├── .streamlit/config.toml
├── docs/
└── dados/
```

Confirme os nomes dos módulos de entradas e os arquivos efetivamente presentes no repositório antes da distribuição. O banco, as fotografias armazenadas e os logs fazem parte do **SQLite**, não devem ser incluídos no Git. O diretório `dados/` deve permanecer persistente no servidor.

## 3. Caminho do banco e separação de ambientes

A aplicação obtém o caminho do banco por meio da variável de ambiente **`PRESTSERV_DB_PATH`**, quando definida; caso contrário, utiliza o caminho padrão configurado em `database.py`, normalmente `dados/PrestServ.db`.

No Linux, maiúsculas e minúsculas no caminho importam. O nome **`prestserv.db`** dentro do ZIP de backup é uma convenção do arquivo compactado e não implica que o banco de produção tenha esse mesmo nome.

A configuração de desenvolvimento usada nos testes é, por exemplo:

```bash
export PRESTSERV_DB_PATH="$PWD/dados/PrestServ_dev.db"
```

**Nunca execute testes de migração ou restauração contra o caminho de produção.** Utilize sempre um banco copiado para uma área separada e configure explicitamente a variável de ambiente.

## 4. Ambiente Python e dependências

No Linux, a partir da raiz do repositório:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

No Windows, o ambiente pode ser ativado com `.venv\Scripts\Activate.ps1`. Confirme a compatibilidade das dependências com a versão de Python usada no Docker; versões geradas em outro Python não garantem uma construção equivalente.

Para iniciar localmente **apenas com o banco de testes configurado**:

```bash
PRESTSERV_DB_PATH="$PWD/dados/PrestServ_dev.db" python -m streamlit run app.py
```

## 5. Criação de uma instalação nova

Para uma instalação sem banco existente, configure o caminho correto e inicialize a estrutura pelo processo previsto no repositório:

```bash
python inicializar_banco.py
python criar_admin.py
```

A criação inicial deve configurar a conta **superadmin** e disponibilizar as tabelas do esquema V2, inclusive cadastros, atendimentos, serviços, quantidades, entradas, voluntários, presenças de voluntários, fotos e logs.

**Não execute esses comandos em produção antes de confirmar como o diretório persistente está montado.** A aplicação também chama `inicializar_banco()` no fluxo de inicialização normal.

## 6. Versão do esquema e migração controlada

A V2 trabalha com `PRAGMA user_version = 2` no SQLite. Esse número é a versão **do esquema do banco**, não a versão do software. Bancos de versões anteriores exigem migração controlada.

O `inicializar_banco.py` da V2 foi preparado para **recusar a inicialização de um banco existente que não esteja no esquema esperado**. Essa proteção evita alterações implícitas em um banco antigo e não deve ser contornada alterando manualmente `PRAGMA user_version`.

### 6.1. Verificar a situação da produção (somente leitura)

Identifique o caminho de dados real do contêiner e faça uma cópia de segurança. Em um ambiente de inspeção apropriado, verifique:

```sql
PRAGMA user_version;
PRAGMA integrity_check;
PRAGMA foreign_key_check;
```

Registre também as tabelas e colunas existentes. A produção pode estar na V1.0 ou em um estado intermediário da V1.1.0; **não presuma a origem sem inspecionar o arquivo efetivamente implantado**.

### 6.2. Homologar em uma cópia isolada

1. **Interrompa escritas** no momento de capturar o estado de produção. Gere um backup consistente usando o procedimento disponível na versão em funcionamento ou a API de backup do SQLite; não copie um banco em uso de maneira insegura.
2. Preserve o arquivo original em armazenamento independente, com identificação e acesso restrito.
3. Restaure essa cópia em diretório de testes, apontando `PRESTSERV_DB_PATH` somente para esse arquivo.
4. Inspecione `user_version`, tabelas, campos e contagens de registros; confira a origem exata do banco.
5. Execute os módulos/scripts **de migração aprovados para essa origem**. O código de migração deve preservar IDs, hashes de senha, serviços, pessoas, fotos, vínculos, datas, logs e demais registros existentes. Não se deve simplesmente criar um banco vazio V2 no lugar do original.
6. Execute as verificações de integridade e compare contagens e registros de amostra antes e depois.
7. Inicie a aplicação V2 apontada para a cópia migrada, teste os cinco perfis e as operações principais.

**Bloqueio de publicação:** este conjunto documental não fornece um comando universal para migrar V1 -> V2. A migração específica depende do esquema e da origem reais. A passagem em produção só pode ocorrer depois de existir um procedimento testado de ponta a ponta sobre uma cópia fiel.

### 6.3. Critérios de aprovação

- `PRAGMA user_version` igual a `2` no banco migrado.
- `PRAGMA integrity_check` retornando `ok`.
- `PRAGMA foreign_key_check` sem resultados.
- Contagens e amostras de pessoas, fotos, serviços, presenças, usuários e logs preservadas; conferência de campos novos e valores padrão.
- Pelo menos um superadministrador ativo e contas dos demais perfis configuradas conscientemente.
- Backup da V2 validado e restauração testada na cópia isolada, sem alteração do banco original.

## 7. Controle de acesso da V2

A aplicação possui cinco papéis: `superadmin`, `admin`, `secretaria`, `porteiro`, `consulta`. O superadmin administra usuários, logs e backup; o admin opera cadastros, correções e relatórios; secretaria opera cadastros e entradas; porteiro registra presenças somente do dia; consulta acessa apenas dados agregados.

As permissões devem ser verificadas novamente nas funções que consultam ou alteram o banco, não apenas na visibilidade do menu. Testes de papéis não devem depender de um usuário autenticado por interface em produção.

## 8. Backup e restauração

### 8.1. Backup

O módulo `backup.py` prepara uma cópia consistente do SQLite e a inclui em um arquivo ZIP, com arquivo interno `prestserv.db`. Na V2, o backup contém as tabelas operacionais e também os dados de **voluntários, fotografias de voluntários e presenças de voluntários**.

A geração de backup completo pela interface é restrita ao **superadministrador**. Os ZIPs contêm dados pessoais, informações cadastrais e hashes de senha; devem ser guardados de maneira protegida, preferencialmente fora do servidor principal. Não os envie ao Git.

### 8.2. Validação e restauração

Antes de restaurar, a aplicação valida a estrutura esperada do banco V2, sua integridade e a autorização do operador. A falta de tabelas essenciais do voluntariado impede a restauração.

A restauração **substitui o conteúdo atual**: operações realizadas após o backup restaurado podem se perder. Não execute a restauração enquanto outros usuários estiverem atendendo. Reautentique e confira dados e logs após a operação.

Nos testes isolados da V2, foram validadas preservação de cadastros, fotos e presenças de voluntários, bloqueio para o perfil Consulta, auditoria de restauração e rejeição de backups incompletos. **Esses testes não substituem a homologação do banco real migrado.**

## 9. Implantação com Docker e Nginx

A infraestrutura institucional mencionada utiliza contêiner Docker, acesso externo via Nginx e armazenamento persistente. Os nomes efetivos dos contêineres, serviços, volumes, diretórios e portas **precisam ser conferidos no servidor** antes de qualquer execução.

Fluxo seguro:

1. Inventariar a implantação atual: imagem, tag, `Dockerfile` ou Compose, volumes, variável `PRESTSERV_DB_PATH`, portas e configuração do Nginx, incluindo WebSocket.
2. Construir a nova imagem a partir de um commit identificado e testar em homologação, **sem montar o volume de produção**.
3. Preparar o banco V2 migrado em ambiente isolado e validar a aplicação com os cinco perfis.
4. Programar janela de manutenção, interromper atendimentos e gerar um **último backup consistente de produção**.
5. Manter a imagem anterior e o banco original preservados para retorno seguro. Planejar a substituição do banco somente depois de validar o resultado da migração final.
6. Atualizar o contêiner e confirmar que a montagem persistente aponta para o banco correto. Reiniciar/recarregar o proxy apenas se houver alteração necessária de configuração.
7. Testar login, presença, voluntários, entradas, relatórios, arquivos exportados, backup, restauração em cópia e logs. Confirmar acesso por celular e WebSocket.
8. Registrar a versão/commit implantado; então concluir a publicação/tag `v2.0.0` conforme o procedimento do repositório.

**Retorno à versão anterior:** não inicie a aplicação antiga sobre um esquema V2 e não altere o banco V2 para fingir que é V1. Para retornar, pare os serviços, restaure o **banco original preservado**, suba a imagem anterior e valide as operações. Alterações realizadas após a migração exigirão conciliação manual se a reversão for necessária.

Não incluímos comandos `docker rm`, `docker volume rm`, `docker compose down -v` nem caminhos de produção não confirmados, pois eles podem causar perda de dados.

## 10. Temas e identidade visual

Os temas claro e escuro são configurados em `.streamlit/config.toml` pelas seções `[theme]`, `[theme.light]` e `[theme.dark]`. A aplicação conserva tipografia e tamanhos dos títulos e indicadores; o usuário pode selecionar tema claro, escuro ou do sistema no menu do Streamlit.

O CSS do rodapé da sidebar usa a cor de fundo do tema. Os relatórios institucionais em PDF mantêm estilo próprio em cinza, independentemente do tema do navegador.

## 11. Git e proteção de arquivos

Confirme que o `.gitignore` protege, no mínimo:

```gitignore
.venv/
__pycache__/
*.pyc
dados/
backups/
*.db
*.db-wal
*.db-shm
*.db-journal
.env
.streamlit/secrets.toml
```

O `.gitignore` não remove dados já incluídos em commits anteriores. Revise o histórico em caso de vazamento. Guarde backups, credenciais e dados pessoais fora de repositórios públicos.

## 12. Checklist de liberação da V2.0.0

- [ ] Testar o código da versão final com os arquivos e dependências que serão publicados.
- [ ] Identificar o esquema e o caminho reais do banco de produção.
- [ ] Validar um procedimento específico de migração da origem real para `user_version = 2` em cópia isolada.
- [ ] Confirmar integridade, relações e preservação de dados após migração.
- [ ] Conferir contas dos cinco perfis, restrição de datas e autorização para refeição no local.
- [ ] Conferir cadastros, entradas, presença de pessoas, quantidades e voluntariado.
- [ ] Testar relatórios CSV/PDF, ranking, certificados e auditoria de downloads.
- [x] Validar backup e restauração V2 em banco temporário com voluntários, fotos e presenças.
- [ ] Validar montagem persistente, imagem Docker e Nginx/WebSocket em homologação.
- [ ] Gerar e proteger backup consistente imediatamente antes da implantação.
- [ ] Publicar/etiquetar a versão somente após liberação técnica e teste do ambiente final.

## 13. Diagnóstico de falhas

**Erro de versão do esquema:** o banco é antigo ou incompatível; não altere `user_version` manualmente. Verifique o procedimento de migração.

**Banco não encontrado:** confira `PRESTSERV_DB_PATH`, o nome do arquivo (inclusive maiúsculas/minúsculas) e a montagem do volume.

**`database is locked`:** verifique acessos concorrentes, transações longas e operações de backup/restauração. Não sobrescreva o SQLite enquanto está em uso.

**Falha no Nginx/WebSocket:** confira proxy reverso, cabeçalhos de upgrade, origem da rota e portas internas da aplicação.

**PDF com fonte ou acentos incorretos:** confira fontes do ReportLab para os relatórios da aplicação, e Pandoc/XeLaTeX, `estilo_pdf.tex` e pacotes de idioma para os manuais.

**Tema não alterna:** confirme o `.streamlit/config.toml` da imagem executada e reinicie o serviço após editar a configuração.

## 14. Autoria e responsabilidade

**Desenvolvido por Jeronimo Costa Penha.** A instituição é responsável pelas políticas locais de acesso, guarda de backups, privacidade, manutenção e continuidade operacional.
