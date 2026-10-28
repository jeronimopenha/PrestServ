# Manual completo do PrestServ

**Versão 1.0 - documentação para uso e administração**  
**Desenvolvido por Jeronimo Costa Penha**

Este manual reúne a apresentação do sistema, as orientações para o porteiro, as funções administrativas e os cuidados de instalação e manutenção.

---


## Apresentação do PrestServ

**Versão de referência:** 1.0  
**Desenvolvimento:** Jeronimo Costa Penha  
**Finalidade:** registro e acompanhamento de atendimentos sociais

### 1. O que é o PrestServ

O **PrestServ** é uma aplicação de apoio ao registro de atendimentos de uma instituição de assistência social. Ela permite identificar as pessoas cadastradas, registrar os serviços recebidos em determinada data e consultar informações consolidadas sobre os atendimentos realizados.

O sistema foi concebido para uma operação simples, com poucos usuários, evitando burocracia desnecessária durante o atendimento.

**Exemplos de serviços:** jantar, banho e roupas. Os serviços efetivamente disponíveis dependem do cadastro de serviços do banco de dados.

### 2. O que o sistema registra

- **Pessoas:** identificação, documento (quando informado), telefones, contato de referência, situação ativa/inativa e fotografia opcional.
- **Atendimentos:** pessoa, data do atendimento e serviços recebidos.
- **Usuários:** nome, login, perfil, situação ativa/inativa e senha armazenada em forma de hash.
- **Relatórios:** indicadores, frequência, serviços prestados e histórico de atendimentos.

Uma pessoa pode receber vários serviços no mesmo dia, mas terá **uma única presença por data**. Por exemplo, jantar e banho no mesmo dia correspondem a uma presença e dois serviços. Um atendimento sem serviços selecionados não é mantido no banco.

### 3. Perfis de acesso

| Perfil | Atividades principais |
|:--|:--|
| **Porteiro** | Localizar pessoa cadastrada, conferir identificação e registrar ou corrigir serviços na data selecionada. |
| **Administrador** | Todas as atividades do porteiro, além de cadastro de pessoas, gestão de usuários, relatórios e operações administrativas disponíveis na instalação. |

A aplicação não disponibiliza cadastro público de pessoas nem acesso anônimo ao histórico.

### 4. Como o sistema funciona

1. O administrador cria o cadastro inicial da pessoa, preferencialmente com fotografia.
2. O porteiro seleciona a data e localiza a pessoa na lista pesquisável.
3. O porteiro confere os dados e marca os serviços recebidos.
4. Ao salvar, o sistema registra ou atualiza a presença daquela pessoa naquela data.
5. O administrador acompanha os resultados nos relatórios e pode exportá-los.

Caso uma pessoa ainda não esteja cadastrada, o procedimento operacional previsto é anotar o atendimento para posterior cadastro pelo administrador. O porteiro não deve usar o cadastro de outra pessoa para registrar esse atendimento.

### 5. Conceitos dos relatórios

| Indicador | Significado |
|:--|:--|
| **Pessoas distintas** | Número de pessoas diferentes com presença no período. |
| **Presenças** | Número de combinações pessoa + data registradas. |
| **Serviços prestados** | Soma das associações entre presenças e serviços. |
| **Dias com registros** | Datas em que existe ao menos uma presença. |
| **Média por dia registrado** | Presenças divididas pelos dias com registros; não necessariamente dias de funcionamento. |

**Atenção:** não se deve interpretar ausência de registros em uma data como prova de que a instituição funcionou naquele dia e não recebeu ninguém.

### 6. Limites e boas práticas

O PrestServ é um instrumento administrativo, e não substitui políticas institucionais de proteção de dados, procedimentos de acolhimento ou registros obrigatórios de outras áreas. Fotografias, contatos e históricos são dados pessoais: devem ser visualizados apenas por pessoas autorizadas.

O banco SQLite padrão não exige senha para abrir o arquivo diretamente. Por isso, a proteção do computador, as permissões de acesso ao arquivo e o armazenamento seguro de backups são fundamentais.

### 7. Créditos

**Desenvolvido por Jeronimo Costa Penha.**  
PrestServ - documentação da versão 1.0.

\newpage


## Manual do porteiro

**PrestServ 1.0 - operação diária**

### 1. Entrar no sistema

1. Abra o endereço do PrestServ informado pelo administrador, em um navegador do computador ou celular conectado à rede autorizada.
2. Digite seu **login** e sua **senha**.
3. Acesse a tela **Presenças**.

Atenção: nesta versão, atualizar a página com **F5** pode encerrar a sessão e exigir novo login. Isso é esperado. Não compartilhe suas credenciais.

### 2. Registrar um atendimento

1. Na tela **Registro de presenças**, confira a **data do atendimento**. O sistema inicia, em geral, com a data atual.
2. Em **Selecione a pessoa**, clique na lista e comece a digitar o nome. A pesquisa ocorre dentro da própria lista.
3. Confira o nome, os dados apresentados e a fotografia, se houver.
4. Marque os serviços efetivamente recebidos, por exemplo **Jantar**, **Banho** e/ou **Roupas**.
5. Clique no botão de salvar ou atualizar o atendimento.
6. Confira a mensagem de confirmação.

**Exemplo:** Maria recebeu jantar e banho em 28/10/2026. Marque os dois serviços e salve. Isso produz **uma presença e dois serviços**.

### 3. Corrigir um atendimento

É possível voltar a uma pessoa e data já registradas, pois os serviços aparecem selecionados conforme o histórico salvo.

1. Selecione a **data correta**.
2. Selecione a **pessoa correta**.
3. Marque ou desmarque os serviços para refletir o atendimento real.
4. Salve a alteração.

**Importante:** se todos os serviços forem desmarcados e a remoção for confirmada pelo fluxo da tela, a presença daquela pessoa nessa data deixa de existir. Não utilize esse procedimento por engano.

### 4. Registrar atendimento de dia anterior

Use o seletor de data para escolher o dia em que o atendimento realmente ocorreu. A data do atendimento não deve ser confundida com o dia em que você está digitando a informação.

Se um atendimento de ontem for registrado hoje, escolha **ontem** como data antes de salvar.

### 5. Pessoa não localizada

Se a pessoa não aparecer na lista:

1. Verifique a grafia do nome e tente pesquisar novamente.
2. Não registre o atendimento em nome de outra pessoa.
3. Avise o administrador e anote os dados necessários conforme o procedimento interno da instituição.
4. Após o cadastro, faça o lançamento com a data correta.

Uma pessoa desativada não aparece na lista de atendimento. A reativação depende do administrador.

### 6. Cuidados durante o uso

- Confira a identidade antes de marcar serviços, especialmente quando houver nomes parecidos.
- Evite deixar o sistema aberto em equipamento compartilhado.
- Use **Sair** ao terminar seu turno.
- Não fotografe nem compartilhe a tela com dados de pessoas atendidas.
- Em caso de instabilidade, confirme se o registro foi salvo antes de repetir a operação.
- Em caso de dúvida sobre correção ou cadastro, procure o administrador.

### 7. Dúvidas frequentes

**A mesma pessoa pode receber dois serviços?** Sim. Marque todos os serviços efetivamente prestados.

**Posso registrar duas presenças para a mesma pessoa no mesmo dia?** Não. O sistema mantém uma presença por pessoa e data e atualiza os serviços correspondentes.

**A página recarregou e pediu login novamente. Perdi o atendimento?** Se o registro já havia sido salvo, ele permanece no banco. Entre novamente e consulte a data e a pessoa para conferir.

**Posso cadastrar pessoas?** Não com o perfil de porteiro. Solicite o cadastro ao administrador.

**Quem pode ver relatórios?** Na configuração prevista para a versão 1.0, o acesso à área de relatórios é administrativo.

### 8. Roteiro rápido para o posto de atendimento

**Data correta → Pessoa correta → Conferir identificação → Marcar serviços → Salvar → Conferir confirmação.**

\newpage


## Manual do administrador

**PrestServ 1.0 - cadastros, usuários, relatórios e dados**

### 1. Responsabilidades do administrador

O administrador organiza os cadastros e acessos, revisa registros quando necessário, consulta relatórios e mantém cópias de segurança dos dados. O uso dessa conta deve ser restrito às pessoas formalmente autorizadas.

### 2. Cadastro de pessoas

Acesse **Cadastros**. A tela contém áreas para criar e consultar/editar registros.

#### 2.1. Novo cadastro

1. Abra **Novo cadastro**.
2. Informe obrigatoriamente o **nome**.
3. Preencha, quando disponíveis, documento, telefone e contato de referência.
4. Adicione fotografia opcional em formato aceito pelo sistema.
5. Salve o cadastro e confira a confirmação.

As imagens são convertidas para JPEG redimensionado antes do armazenamento no banco. A fotografia serve para auxiliar a identificação; não substitui a confirmação por outros meios quando necessária.

#### 2.2. Alterar cadastro

1. Abra **Consultar / editar**.
2. Localize a pessoa por nome ou identificador.
3. Revise os dados e salve as alterações.
4. Se necessário, envie uma nova fotografia ou utilize a opção de remover fotografia mediante confirmação.

#### 2.3. Desativar e reativar

A desativação retira a pessoa das opções de novos atendimentos, mas **não apaga seu histórico**. Use-a quando apropriado e reative a pessoa se for necessário voltar a atendê-la. Evite criar cadastro duplicado.

### 3. Administração de usuários

Na área **Administração**, o administrador pode criar contas e, conforme os controles disponíveis na versão instalada, editar nome, login, perfil, situação e redefinir senhas.

| Campo | Boa prática |
|:--|:--|
| Nome | Usar identificação reconhecível do funcionário ou colaborador. |
| Login | Manter identificador individual e único. |
| Senha | Fornecer de modo reservado; o sistema armazena apenas o hash. |
| Perfil | Conceder apenas as permissões necessárias. |
| Situação | Desativar quem não precisa mais acessar; evitar apagar históricos. |

Nunca use uma conta compartilhada se for importante identificar qual operador realizou um atendimento. Não é possível recuperar a senha original pelo hash; a solução é **redefini-la**.

### 4. Relatórios

Acesse **Relatórios** e escolha o período. É possível usar atalhos para o mês, semestre e ano ou informar datas personalizadas.

#### 4.1. Filtrar informações

O filtro **Pessoa** permite selecionar uma pessoa específica ou todas as pessoas. O intervalo inclui as datas inicial e final.

#### 4.2. Indicadores

- **Pessoas distintas:** quantidade de pessoas atendidas no período, independentemente do número de visitas.
- **Presenças:** quantidade de registros pessoa/data no período.
- **Serviços prestados:** quantidade total de serviços associados às presenças.
- **Dias com registros:** quantidade de datas com presenças.
- **Média por dia registrado:** presenças divididas pelos dias com registros.

#### 4.3. Relatórios disponíveis

- **Visão geral:** distribuição de serviços e evolução diária/mensal.
- **Frequência:** número de presenças por pessoa e datas de primeira/última presença no intervalo.
- **Histórico:** linhas individuais por atendimento, com os serviços associados.
- **Ausências:** pessoas ativas sem atendimento nos últimos X dias ou sem atendimento anterior até a data de referência.
- **Cadastros:** informação sobre campos preenchidos e disponibilidade de fotografia.

**Interpretação:** uma pessoa com três presenças e sete serviços representa três dias de comparecimento e sete serviços registrados; não são sete visitas.

#### 4.4. Exportar

Use os botões de **CSV** nas seções de tabela ou selecione o conteúdo no campo de exportação e clique em **Baixar relatório em PDF**.

O PDF tem aparência institucional, em tons de cinza, e identifica **Jeronimo Costa Penha** como desenvolvedor. Os gráficos podem aparecer na tela; sua inclusão no PDF depende da versão instalada.

**Privacidade:** antes de compartilhar um PDF ou CSV, verifique se o destinatário está autorizado a receber nomes e histórico de pessoas atendidas. Sempre que possível, prefira dados agregados.

### 5. Backup por download

O PrestServ foi planejado para produzir backup **sob demanda, por download**, sem guardar cópias permanentes na pasta do servidor.

1. Entre com uma conta administrativa.
2. Acesse **Backup e restauração** (se a função já estiver habilitada na instalação).
3. Clique em **Preparar backup**.
4. Clique em **Baixar backup**.
5. Guarde o arquivo `.db` em local seguro, preferencialmente fora do computador que executa o sistema.
6. Confirme que o download foi concluído e que o arquivo está acessível.

O backup inclui cadastros, fotografias, atendimentos e contas de usuário. **Ele contém dados pessoais e hashes de senhas; trate-o como informação confidencial.**

Sugestão operacional: realizar o download em uma frequência definida pela instituição, por exemplo após cada dia de atendimento, e guardar mais de uma geração em locais protegidos.

### 6. Restauração por upload

**Advertência:** restaurar um backup substitui os dados existentes pelo conteúdo do arquivo escolhido. Registros criados após a data daquele backup podem ser perdidos.

Procedimento seguro:

1. Planeje uma janela de manutenção e interrompa o uso por todos os operadores.
2. Faça e baixe um backup do estado atual antes da restauração.
3. Na área **Restaurar backup**, selecione o arquivo `.db`.
4. Confira nome e tamanho e confirme conscientemente a substituição.
5. Execute a restauração somente com todas as conexões de atendimento encerradas e com o procedimento técnico de manutenção validado.
6. Reabra o sistema, autentique-se novamente e confira cadastros, fotos e atendimentos de amostra.

**Não faça uma restauração em produção enquanto houver usuários trabalhando.** A presença de um aviso na tela, por si só, não garante que outras sessões foram interrompidas. O mecanismo de bloqueio/manutenção deve ser testado antes de liberar esta função.

### 7. Proteção dos dados

- Restrinja o acesso à máquina e à pasta que contém `prestserv.db`.
- Não envie o banco real, backups ou relatórios pessoais para um repositório público.
- Proteja os arquivos baixados e elimine cópias desnecessárias de forma apropriada.
- Exija credenciais individuais e desative acessos não utilizados.
- Evite abrir o PrestServ em rede pública sem medidas adicionais de proteção.
- O SQLite padrão **não possui senha de acesso ao arquivo**; o login do PrestServ protege a interface, não a leitura direta do arquivo por quem tem permissões no sistema operacional.

### 8. Verificação rotineira

Antes de iniciar as atividades: confirmar acesso dos usuários, data do sistema e disponibilidade da aplicação. Ao final: conferir os lançamentos do dia e executar o procedimento institucional de backup. Periodicamente: revisar cadastros duplicados/inativos, permissões de usuários e qualidade dos dados.

### 9. O que não deve ser presumido nesta versão

A documentação não afirma que exista auditoria imutável de ações, expiração de sessão, backup automático ou criptografia do arquivo SQLite. Essas funções devem ser consideradas **indisponíveis** até serem expressamente implementadas e testadas.

\newpage


## Instalação e manutenção técnica

**PrestServ 1.0 - orientações para o responsável técnico**

### 1. Arquitetura resumida

O PrestServ usa **Python**, **Streamlit** (interface web), **SQLite** (persistência) e **Pillow** (tratamento de fotografias). Os relatórios usam **pandas** e **ReportLab**. O navegador acessa o serviço Streamlit executado na máquina que hospeda a aplicação.

O mesmo projeto pode ser usado localmente ou em uma rede controlada. A implantação final em Windows depende da configuração da máquina e da distribuição escolhida.

### 2. Estrutura sugerida do projeto

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

### 3. Preparar o ambiente

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

### 4. Criar automaticamente o banco

Ao iniciar a instalação, `inicializar_banco.py` deve criar a pasta `dados/`, o arquivo `prestserv.db`, tabelas, índices e serviços iniciais **se não existirem**, sem sobrescrever bancos anteriores.

Execução manual inicial:

```bash
python inicializar_banco.py
```

O `app.py` também pode chamar `inicializar_banco()` antes de acessar o banco.

**Aviso:** `CREATE TABLE IF NOT EXISTS` inicializa bancos novos, mas **não migra** automaticamente alterações de estrutura de versões futuras. Migrações precisarão de scripts próprios.

### 5. Criar a primeira conta administrativa

Depois de inicializar um banco novo, execute:

```bash
python criar_admin.py
```

O programa solicita os dados da primeira conta. Conforme o mecanismo atual, a criação inicial é bloqueada quando já existe algum usuário. Mantenha a senha em sigilo e teste o acesso antes de liberar a aplicação.

### 6. Executar o sistema

```bash
python -m streamlit run app.py
```

O Streamlit geralmente usa a porta `8501`, salvo configuração em contrário. Para acesso em outros dispositivos da rede, defina endereço de escuta e regras de firewall apropriados. **Não publique diretamente na internet uma instalação pensada somente para rede local.**

Se a página for atualizada com **F5**, a autenticação armazenada em `st.session_state` pode ser perdida e será necessário entrar novamente. Isso não indica perda dos registros já salvos.

### 7. Banco SQLite

O caminho padrão do banco é definido em `database.py` e aponta para `dados/prestserv.db` em relação à pasta do projeto. Cada conexão deve ativar as chaves estrangeiras:

```sql
PRAGMA foreign_keys = ON;
```

O arquivo `.db` contém também as fotografias. Portanto, copiá-lo ou compartilhá-lo equivale a copiar dados pessoais e registros de usuários.

### 8. Backup e restauração

A estratégia prevista é **backup por download** e **restauração por upload**, sem diretório persistente de backups no servidor.

- **Backup:** use a API `sqlite3.Connection.backup()` para gerar uma cópia consistente antes de disponibilizá-la ao navegador.
- **Restauração:** valide o arquivo recebido, estrutura e integridade antes da substituição. Execute em janela de manutenção, sem operadores conectados.
- **Retomada:** reinicie a aplicação e reautentique os usuários após uma restauração bem-sucedida.

**Teste obrigatório:** executar um ciclo completo de backup e restauração em uma base de teste, incluindo fotos, usuários e presenças. Não confiar apenas no recebimento do arquivo.

### 9. Git e exclusão de dados

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

### 10. Validação pré-lançamento

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

### 11. Diagnóstico de problemas

**Banco não encontrado:** confira se `inicializar_banco()` foi chamado e se a aplicação tem permissão para criar `dados/`.

**Login recusado:** confira usuário ativo, login e senha; não edite o hash manualmente.

**Foto não aparece:** confira se existe registro em `fotos_pessoas` e se o envio foi convertido com sucesso.

**Erro de banco bloqueado (`database is locked`):** verifique conexões duradouras, transações abertas e operações simultâneas; não force substituição do banco enquanto ele está em uso.

**PDF com cabeçalho ilegível:** verifique se o estilo dos `Paragraph` de cabeçalho foi configurado com texto branco, além do fundo cinza-escuro da tabela.

### 12. Suporte e autoria

Código, documentação e interface desenvolvidos por **Jeronimo Costa Penha**. Os procedimentos locais de suporte e guarda de dados devem ser definidos pela instituição que utiliza o PrestServ.

\newpage
