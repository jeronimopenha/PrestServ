# Instalação e manutenção técnica

**PrestServ 1.0 - orientações para o responsável técnico**

## 1. Arquitetura resumida

O PrestServ usa **Python**, **Streamlit** (interface web), **SQLite** (persistência) e **Pillow** (tratamento de fotografias). Os relatórios usam **pandas** e **ReportLab**. O navegador acessa o serviço Streamlit executado na máquina que hospeda a aplicação.

O mesmo projeto pode ser usado localmente ou em uma rede controlada. A implantação final em Windows depende da configuração da máquina e da distribuição escolhida.

## 2. Estrutura sugerida do projeto

```text
prestserv/
├── app.py
├── auth.py
├── database.py
├── inicializar_banco.py
├── criar_admin.py
├── presencas.py
├── cadastros.py
├── relatorios.py
├── consultas_relatorios.py
├── pdf_relatorios.py
├── fotos.py
├── backups.py
├── tela_backups.py
├── docs/
│   ├── visao_geral.md
│   ├── manual_porteiro.md
│   ├── manual_administrador.md
│   └── instalacao_manutencao.md
├── dados/                 # Criada localmente; não versionar
│   └── prestserv.db       # Dados reais; não versionar
└── .gitignore
```

Os nomes dos arquivos refletem o planejamento atual; confira o repositório antes de usar instruções de instalação automatizada.

## 3. Preparar o ambiente

Exemplo para instalação direta com Python:

```bash
python -m venv .venv
```

No Linux:

```bash
source .venv/bin/activate
```

No Windows (PowerShell):

```powershell
.venv\Scripts\Activate.ps1
```

Instale as dependências:

```bash
python -m pip install streamlit pillow pandas reportlab
```

O ideal para distribuição é manter um arquivo `requirements.txt` com versões testadas e instalar por `python -m pip install -r requirements.txt`.

## 4. Criar automaticamente o banco

Ao iniciar a instalação, `inicializar_banco.py` deve criar a pasta `dados/`, o arquivo `prestserv.db`, tabelas, índices e serviços iniciais **se não existirem**, sem sobrescrever bancos anteriores.

Execução manual inicial:

```bash
python inicializar_banco.py
```

O `app.py` também pode chamar `inicializar_banco()` antes de acessar o banco.

**Aviso:** `CREATE TABLE IF NOT EXISTS` inicializa bancos novos, mas **não migra** automaticamente alterações de estrutura de versões futuras. Migrações precisarão de scripts próprios.

## 5. Criar a primeira conta administrativa

Depois de inicializar um banco novo, execute:

```bash
python criar_admin.py
```

O programa solicita os dados da primeira conta. Conforme o mecanismo atual, a criação inicial é bloqueada quando já existe algum usuário. Mantenha a senha em sigilo e teste o acesso antes de liberar a aplicação.

## 6. Executar o sistema

```bash
python -m streamlit run app.py
```

O Streamlit geralmente usa a porta `8501`, salvo configuração em contrário. Para acesso em outros dispositivos da rede, defina endereço de escuta e regras de firewall apropriados. **Não publique diretamente na internet uma instalação pensada somente para rede local.**

Se a página for atualizada com **F5**, a autenticação armazenada em `st.session_state` pode ser perdida e será necessário entrar novamente. Isso não indica perda dos registros já salvos.

## 7. Banco SQLite

O caminho padrão do banco é definido em `database.py` e aponta para `dados/prestserv.db` em relação à pasta do projeto. Cada conexão deve ativar as chaves estrangeiras:

```sql
PRAGMA foreign_keys = ON;
```

O arquivo `.db` contém também as fotografias. Portanto, copiá-lo ou compartilhá-lo equivale a copiar dados pessoais e registros de usuários.

## 8. Backup e restauração

A estratégia prevista é **backup por download** e **restauração por upload**, sem diretório persistente de backups no servidor.

- **Backup:** use a API `sqlite3.Connection.backup()` para gerar uma cópia consistente antes de disponibilizá-la ao navegador.
- **Restauração:** valide o arquivo recebido, estrutura e integridade antes da substituição. Execute em janela de manutenção, sem operadores conectados.
- **Retomada:** reinicie a aplicação e reautentique os usuários após uma restauração bem-sucedida.

**Teste obrigatório:** executar um ciclo completo de backup e restauração em uma base de teste, incluindo fotos, usuários e presenças. Não confiar apenas no recebimento do arquivo.

## 9. Git e exclusão de dados

Regras recomendadas para `.gitignore`:

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

Se dados sensíveis já tiverem sido publicados anteriormente, `.gitignore` **não apaga o histórico de commits**. Essa situação exige tratamento específico.

## 10. Validação pré-lançamento

- [ ] Banco criado automaticamente em instalação limpa.
- [ ] Conta de administrador inicial criada e autenticação validada.
- [ ] Porteiro vê somente as funções previstas para seu perfil.
- [ ] Cadastro, alteração e desativação de pessoas testados.
- [ ] Fotografia enviada, visualizada, substituída e removida.
- [ ] Atendimento criado, corrigido, retroativo e removido conforme regra de serviços.
- [ ] Indicadores e totais dos relatórios conferidos com o SQLite.
- [ ] PDF e CSV testados com acentos e dados extensos.
- [ ] Backup baixado e validado.
- [ ] Restauração testada com o sistema parado e base descartável.
- [ ] Pastas e permissões do Windows verificadas.
- [ ] Documentação revisada a partir da interface realmente instalada.

## 11. Diagnóstico de problemas

**Banco não encontrado:** confira se `inicializar_banco()` foi chamado e se a aplicação tem permissão para criar `dados/`.

**Login recusado:** confira usuário ativo, login e senha; não edite o hash manualmente.

**Foto não aparece:** confira se existe registro em `fotos_pessoas` e se o envio foi convertido com sucesso.

**Erro de banco bloqueado (`database is locked`):** verifique conexões duradouras, transações abertas e operações simultâneas; não force substituição do banco enquanto ele está em uso.

**PDF com cabeçalho ilegível:** verifique se o estilo dos `Paragraph` de cabeçalho foi configurado com texto branco, além do fundo cinza-escuro da tabela.

## 12. Suporte e autoria

Código, documentação e interface desenvolvidos por **Jeronimo Costa Penha**. Os procedimentos locais de suporte e guarda de dados devem ser definidos pela instituição que utiliza o PrestServ.
