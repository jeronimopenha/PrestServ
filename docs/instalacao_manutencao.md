---
title: "Instalação e manutenção técnica"
subtitle: "PrestServ 1.1.0 — orientações para o responsável técnico"
author: "Jeronimo Costa Penha"
date: "Novembro de 2026"
lang: pt-BR
---

## 1. Arquitetura e funcionamento

O PrestServ utiliza **Python**, **Streamlit** (interface web), **SQLite** (persistência), **Pillow** (tratamento de fotografias), **pandas** (consultas e tabelas) e **ReportLab** (relatórios em PDF). Pode ser executado diretamente em ambiente Python ou em contêiner Docker. Na implantação atualmente utilizada, o serviço é acessado por um proxy reverso Nginx.

Existem dois perfis de usuário: `admin` e `porteiro`. A aplicação guarda os usuários no banco SQLite; a autenticação pela interface não cifra o arquivo físico.

## 2. Organização dos arquivos

A estrutura principal inclui os seguintes arquivos (além de outros módulos auxiliares):

```text
PrestServ/
├── app.py
├── auth.py
├── backup.py
├── cadastros.py
├── common.py
├── consultas_relatorios.py
├── criar_admin.py
├── database.py
├── estrutura_v110.py
├── fotos.py
├── inicializar_banco.py
├── pdf_relatorios.py
├── presencas.py
├── relatorios.py
├── tela_backups.py
├── tela_logs.py
├── requirements.txt
├── docs/
│   ├── README.md
│   ├── visao_geral.md
│   ├── manual_porteiro.md
│   ├── manual_administrador.md
│   ├── instalacao_manutencao.md
│   ├── manual_completo.md
│   ├── estilo_pdf.tex
│   └── gerar_manuais.sh
└── dados/
    └── PrestServ.db
```

**Importante (Linux):** o caminho real do banco é definido em `database.py` como `dados/PrestServ.db`, com letras maiúsculas. O nome interno **`prestserv.db`** do ZIP é diferente por convenção e não deve ser usado para substituir o caminho real de produção.

A pasta `dados/` e seus arquivos não devem ser enviados para repositórios públicos.

## 3. Preparar o ambiente Python

Crie e ative um ambiente virtual na raiz do projeto:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

No Windows PowerShell, a ativação correspondente é `.venv\Scripts\Activate.ps1`.

O `requirements.txt` deve registrar versões verificadas e compatíveis com o **Python da imagem Docker utilizada**. Um arquivo gerado em ambiente Python 3.14 não garante, por si só, instalação compatível em uma imagem Python 3.12; valide a construção do contêiner antes da publicação.

## 4. Inicializar o banco e criar o administrador inicial

Execute:

```bash
python inicializar_banco.py
python criar_admin.py
```

A primeira execução cria as tabelas de pessoas, serviços, presenças, usuários e fotografias, com os serviços iniciais **Jantar**, **Banho** e **Roupas**. `criar_admin.py` configura a conta administrativa inicial. Guarde as credenciais com segurança.

Na execução normal, `app.py` também chama `inicializar_banco()` antes de disponibilizar as telas.

## 5. Migração de esquema na V1.1.0

O módulo `estrutura_v110.py` cria a tabela `logs` e os índices associados, sem apagar os registros existentes. A migração é chamada pela inicialização do banco e define `PRAGMA user_version = 1` na implementação atual.

- **Banco novo:** a tabela de logs é preparada durante a inicialização.
- **Banco V1.0 existente:** a estrutura de auditoria é criada, preservando os cadastros, usuários e atendimentos existentes.
- **Executar novamente:** a migração foi projetada para ser repetida sem recriar a tabela ou descartar os dados existentes.

A migração foi testada com uma cópia isolada do banco, incluindo verificação de integridade. **Isso não representa um mecanismo genérico de migração para todas as versões futuras**: alterações posteriores exigirão validações próprias.

Não altere manualmente o número `user_version` para simular uma migração de produção sem respaldo técnico.

## 6. Executar a aplicação

```bash
python -m streamlit run app.py
```

O Streamlit utiliza normalmente a porta **8501**, salvo configuração em contrário. Controle acesso, firewall e regras do proxy reverso conforme a instalação. O encerramento ou recarregamento de uma sessão pode exigir novo login; atendimentos já salvos permanecem no banco.

Na versão preparada para publicação, os administradores podem acessar **Presenças**, **Cadastros**, **Relatórios**, **Logs do sistema**, **Backup e restauração** e **Administração**; o porteiro acessa a operação de presenças.

## 7. Banco SQLite e integridade

O arquivo padrão é `dados/PrestServ.db`. Cada conexão operacional deve ativar:

```sql
PRAGMA foreign_keys = ON;
```

Comandos úteis para verificar uma cópia do banco:

```sql
PRAGMA user_version;
PRAGMA integrity_check;
PRAGMA foreign_key_check;
```

Resultado esperado após migração: `user_version = 1`, `integrity_check = ok` e nenhuma violação em `foreign_key_check`.

A tabela `logs` guarda data/hora em UTC, operador, tipo de ação, entidade afetada, resultado e detalhes em JSON quando disponíveis. A interface exibe datas no horário de Brasília. Como os logs não possuem chave estrangeira para `usuarios`, podem sobreviver à exclusão de uma conta.

## 8. Exclusões e auditoria

A verificação de vínculos antes de excluir pessoas ou usuários é implementada em `estrutura_v110.py` e aplicada novamente no momento da exclusão. Pessoas com fotografias ou atendimentos vinculados não podem ser excluídas por esse fluxo. O último administrador ativo e a própria conta administrativa estão protegidos contra exclusão.

A rotina de limpeza de logs limita a operação a **500 IDs**, valida autorização e registra a exclusão. **Não considere os logs uma auditoria imutável**, pois um administrador autorizado pode excluí-los pela interface.

Os registros de auditoria podem conter informações administrativas e identificadores pessoais. Controle seu acesso e não os publique.

## 9. Backup e restauração

### 9.1. Gerar backup

O módulo `backup.py` gera em memória uma cópia consistente do SQLite com `sqlite3.conn.backup()`, compactada em ZIP. O nome do arquivo interno é **`prestserv.db`**. O backup inclui pessoas, usuários, fotografias, atendimentos e logs existentes no momento da geração.

A interface administrativa oferece **Preparar backup** e **Baixar backup ZIP**. Não há necessidade de uma pasta persistente de backups no servidor para este procedimento; a política de armazenamento externo é responsabilidade da instituição.

### 9.2. Restaurar backup

A restauração aceita ZIP no formato previsto e valida arquivo, tabelas obrigatórias, integridade, relações entre tabelas e existência de administrador ativo antes de substituir o banco. A restauração deve ocorrer **sem atendimentos concorrentes** e com backup prévio do estado atual.

Depois da operação, autentique-se novamente e confira cadastros, pessoas, fotografias, atendimentos e logs. Um backup restaurado pode substituir o histórico atual por um histórico mais antigo; a versão nova registra o evento de restauração no banco restaurado.

### 9.3. Testes realizados na preparação da V1.1.0

- ZIP de backup: verificada a presença de `prestserv.db`.
- Integridade da cópia: `ok` e nenhuma violação de chaves estrangeiras.
- Migração isolada: tabela `logs` recriada, `user_version = 1`, dados preservados.
- Restauração isolada: integridade `ok`, dados preservados e último evento `restaurar_backup`.

Esses resultados foram obtidos em testes locais. Antes da publicação, valide também a imagem Docker e os procedimentos da infraestrutura real.

## 10. Implantação Docker e proxy reverso

A atualização da imagem Docker deve ser executada somente após validar o `requirements.txt` com a versão de Python definida no `Dockerfile` e confirmar a persistência do diretório `dados/` por volume ou montagem equivalente.

Procedimento recomendado:

1. Registrar o estado atual da implantação e obter um backup ZIP íntegro.
2. Construir e testar a nova imagem na branch de desenvolvimento.
3. Verificar a configuração do volume de dados e os parâmetros de rede/proxy.
4. Publicar a tag da versão no repositório e implantar a imagem revisada no Portainer.
5. Verificar login, operações principais, logs, relatórios e backup após a atualização.

**Nunca recrie ou substitua um volume de produção sem garantir a recuperação dos dados.** Esta documentação não pressupõe comandos exatos de Docker Compose ou Portainer, pois dependem dos arquivos reais de implantação.

## 11. Git e proteção de dados

Exemplo de padrões a incluir no `.gitignore`:

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
build/
dist/
```

Um `.gitignore` não remove arquivos sensíveis de commits anteriores; consulte o histórico caso algum dado real já tenha sido publicado.

## 12. Checklist de validação antes da publicação

- [ ] Executar `python -m compileall -q .` sem erros.
- [ ] Confirmar versão do Python e resolver dependências em ambiente compatível com o Docker.
- [ ] Confirmar que o banco real é persistido fora do contêiner efêmero.
- [ ] Validar autenticação e permissões de `admin` e `porteiro`.
- [ ] Conferir criação, edição, ativação, desativação e exclusão condicionada de pessoas e usuários.
- [ ] Conferir fotografia, presenças retroativas e múltiplos serviços.
- [ ] Consultar logs, filtros, detalhes e limpeza de registros selecionados.
- [ ] Conferir indicadores, CSV e PDF.
- [x] Validar backup ZIP, integridade, migração e restauração em cópias isoladas.
- [ ] Fazer backup imediatamente antes da implantação.
- [ ] Testar a versão em produção após atualizar a imagem Docker.

## 13. Diagnóstico de problemas

**Banco não encontrado:** confira `DB_PATH` em `database.py`, inclusive maiúsculas e minúsculas, e a montagem do volume.

**Login recusado:** confira a conta, senha e situação ativa; nunca edite o hash manualmente.

**Foto não aparece:** confira a existência do registro em `fotos_pessoas` e o formato da imagem.

**Banco bloqueado (`database is locked`):** verifique operações simultâneas, transações longas e conexões abertas. Não sobrescreva o arquivo SQLite em uso.

**Avisos `use_container_width`:** substitua parâmetros antigos por `width="stretch"` ou `width="content"` conforme o componente. Esses ajustes foram realizados no código de desenvolvimento antes da preparação da documentação.

**PDF com texto difícil de ler:** confira configuração de fontes, caracteres acentuados e contraste dos cabeçalhos nos estilos do ReportLab.

## 14. Autoria

Código, documentação e interface desenvolvidos por **Jeronimo Costa Penha**. A instituição usuária deve definir as políticas locais de operação, guarda de dados e acesso aos backups.
