---
title: "Manual completo do PrestServ"
subtitle: "Versão 1.1.0 — uso, administração e manutenção"
author: "Jeronimo Costa Penha"
date: "Novembro de 2026"
lang: pt-BR
---


\newpage

## Apresentação do PrestServ

### 1. O que é o PrestServ

O **PrestServ** é uma aplicação de apoio ao registro de atendimentos de uma instituição de assistência social. Ela permite identificar as pessoas cadastradas, registrar os serviços recebidos em determinada data e consultar informações consolidadas sobre os atendimentos realizados.

O sistema foi concebido para uma operação simples, com poucos usuários, evitando burocracia desnecessária durante o atendimento.

**Exemplos de serviços:** jantar, banho e roupas. Os serviços efetivamente disponíveis dependem do cadastro de serviços do banco de dados.

### 2. O que o sistema registra

- **Pessoas:** identificação, documento (quando informado), telefones, contato de referência, situação ativa/inativa e fotografia opcional.
- **Atendimentos:** pessoa, data do atendimento e serviços recebidos.
- **Usuários:** nome, login, perfil, situação ativa/inativa e senha armazenada em forma de hash.
- **Relatórios:** indicadores, frequência, serviços prestados e histórico de atendimentos.
- **Auditoria (V1.1.0):** data e hora das operações, identificação do operador, ação, resultado e detalhes quando disponíveis.

Uma pessoa pode receber vários serviços no mesmo dia, mas terá **uma única presença por data**. Por exemplo, jantar e banho no mesmo dia correspondem a uma presença e dois serviços. Um atendimento sem serviços selecionados não é mantido no banco.

### 3. Perfis de acesso

| Perfil | Atividades principais |
|:--|:--|
| **Porteiro** | Localizar pessoa cadastrada, conferir identificação e registrar ou corrigir serviços na data selecionada. |
| **Administrador** | Todas as atividades do porteiro, além de cadastro de pessoas, gestão de usuários, relatórios, consulta de logs, backup e restauração. |

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

### 7. Auditoria e exclusão (V1.1.0)

As operações relevantes são registradas para facilitar a identificação de alterações. Somente administradores podem consultar e excluir logs pela interface. A exclusão de pessoas e usuários é condicionada aos vínculos existentes; quando um cadastro possui histórico associado, a desativação permite preservá-lo.

**Limite importante:** logs podem ser excluídos por administradores e não constituem trilha de auditoria imutável. Um backup restaurado não preserva automaticamente operações realizadas após a criação desse backup.

### 8. Créditos

**Desenvolvido por Jeronimo Costa Penha.**  
PrestServ - documentação da versão 1.1.0.


\newpage

## Manual do porteiro

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

**Quem pode ver relatórios?** O acesso à área de relatórios é restrito ao administrador.

### 8. Registro das operações

Na V1.1.0, o sistema registra operações relevantes, como entradas, saídas e alterações de atendimentos. A consulta dos logs é restrita ao administrador. Utilize sempre sua própria conta para que seja possível reconhecer o responsável por cada operação.

### 9. Roteiro rápido para o posto de atendimento

**Data correta → Pessoa correta → Conferir identificação → Marcar serviços → Salvar → Conferir confirmação.**


\newpage

## Manual do administrador

### 1. Responsabilidades do administrador

O administrador organiza os cadastros e acessos, revisa atendimentos, acompanha relatórios, consulta o histórico de operações e mantém cópias de segurança. O uso da conta administrativa deve ficar restrito às pessoas autorizadas.

### 2. Cadastro de pessoas

Acesse **Cadastros**, onde estão as áreas **Novo cadastro** e **Consultar / editar**.

#### 2.1. Cadastrar

1. Abra **Novo cadastro** e informe obrigatoriamente o **nome**.
2. Preencha, quando disponíveis, documento, telefone e contato de referência.
3. Acrescente uma fotografia opcional, nos formatos aceitos pela interface.
4. Salve e confira a confirmação.

As fotos são convertidas para JPEG e redimensionadas antes de serem armazenadas no banco. A imagem auxilia a identificação, mas não substitui a conferência de outros dados quando necessário.

#### 2.2. Editar, fotografar e desativar

1. Abra **Consultar / editar** e selecione a pessoa.
2. Altere os dados necessários e salve.
3. Se for o caso, substitua ou remova a fotografia, observando a confirmação exigida na interface.
4. Use **Desativar pessoa** para impedir novos atendimentos sem perder o histórico; **Reativar pessoa** permite voltar a registrar atendimentos.

#### 2.3. Exclusão condicionada (V1.1.0)

A exclusão definitiva só é disponibilizada quando não há relacionamentos que a impeçam. A verificação considera, entre outros, registros de **presença** e **fotografia**. Uma pessoa que possui apenas fotografia também não pode ser excluída enquanto a foto não for removida.

- Se houver histórico de atendimentos, prefira **desativar**: o sistema preserva os registros anteriores.
- Se a pessoa não tiver vínculos impeditivos, o administrador poderá solicitar a exclusão e confirmar a operação.
- A verificação é realizada novamente ao excluir, para evitar inconsistências caso os dados tenham mudado.

**Atenção:** exclusão é permanente. A existência de um log da operação não permite recuperar automaticamente o registro excluído.

### 3. Administração de usuários

Na área **Administração**, o administrador pode criar usuários, editar nome, login e perfil, ativar/desativar contas e redefinir senhas.

| Campo | Boa prática |
|:--|:--|
| Nome | Identificação reconhecível do colaborador. |
| Login | Identificador individual e único. |
| Senha | Entregar reservadamente; o sistema armazena o hash, não a senha original. |
| Perfil | Conceder apenas as permissões necessárias (`admin` ou `porteiro`). |
| Situação | Desativar contas sem uso, preservando o histórico operacional. |

#### 3.1. Exclusão de usuários (V1.1.0)

É possível excluir contas sem vínculos operacionais que impeçam a operação. O sistema aplica proteções adicionais:

- Um administrador não pode excluir a própria conta.
- Não é permitido excluir ou deixar indisponível o último administrador ativo.
- O usuário precisa ter permissão administrativa ativa.
- A exclusão exige confirmação.

Os registros de auditoria guardam o login e o identificador do operador sem criar vínculo de chave estrangeira com a tabela de usuários. Por isso, **logs antigos, por si só, não bloqueiam a exclusão de uma conta**. Eles podem continuar mostrando o login de um usuário já removido.

Não compartilhe contas: os logs dependem da identificação individual. Senhas esquecidas devem ser **redefinidas**, e não recuperadas a partir do hash.

### 4. Relatórios

Acesse **Relatórios**, escolha o período (**Mês atual**, **Semestre atual**, **Ano atual** ou **Personalizado**) e, se necessário, selecione uma pessoa. As datas inicial e final integram o intervalo consultado.

#### 4.1. Indicadores

- **Pessoas distintas:** pessoas diferentes atendidas no período.
- **Presenças:** registros únicos de pessoa e data.
- **Serviços prestados:** quantidade total de serviços associados às presenças.
- **Dias com registros:** quantidade de datas com ao menos uma presença.
- **Média por dia registrado:** presenças divididas pela quantidade de dias registrados.

Por exemplo, três presenças e sete serviços representam **três dias de comparecimento** e **sete serviços prestados**, não sete visitas.

#### 4.2. Consultas e exportação

- **Visão geral:** distribuição de serviços e evolução dos registros.
- **Frequência:** quantidade de presenças por pessoa.
- **Histórico:** atendimentos individuais e respectivos serviços.
- **Ausências:** pessoas ativas sem atendimento recente.
- **Cadastros:** preenchimento de campos e disponibilidade de fotografia.

As tabelas podem oferecer exportação em **CSV**; a tela também permite gerar relatórios em **PDF**, com apresentação institucional em tons de cinza. Antes de compartilhar arquivos, confira se os destinatários estão autorizados a acessar os dados pessoais.

### 5. Logs do sistema (V1.1.0)

Acesse **Logs do sistema** no menu administrativo para consultar eventos de autenticação, cadastros, atendimentos, fotografias, usuários, backups, restaurações e outras operações auditadas.

#### 5.1. Consultar

1. Se necessário, filtre por **operador**, **ação**, **resultado** e **período**.
2. Ajuste o **máximo de registros** exibidos.
3. Consulte a tabela ordenada pelas operações registradas.
4. Na seção **Detalhes da operação**, selecione o ID de um registro para examinar as informações adicionais.

O filtro de **ação** apresenta as ações encontradas no histórico. As datas exibidas na interface são convertidas para o horário de Brasília; o banco armazena os horários de auditoria em UTC.

#### 5.2. Limpar logs selecionados

1. Marque as caixas de seleção dos registros que deseja excluir, ou utilize **Selecionar todos** para selecionar os exibidos.
2. Confira a quantidade selecionada; o limite é de **500 registros por operação**.
3. Marque a confirmação de exclusão definitiva.
4. Clique em **Excluir selecionados**.

A exclusão gera um **novo log `excluir_logs`**, contendo o operador, a quantidade e os identificadores removidos. A operação de limpeza não restaura os eventos apagados.

**Limitação:** a trilha de auditoria não é imutável. Um administrador poderá excluir posteriormente até mesmo o registro de uma limpeza anterior. A exclusão não deve ser tratada como um mecanismo de retenção inviolável.

### 6. Backup por download

Na área **Backup e restauração**, abra a aba de backup:

1. Clique em **Preparar backup**.
2. Clique em **Baixar backup ZIP**.
3. Salve o arquivo `.zip` em local seguro, preferencialmente fora do computador do servidor.
4. Confira o arquivo obtido antes de considerá-lo uma cópia de segurança válida.

O ZIP contém o arquivo **`prestserv.db`**, que inclui cadastros, fotos, atendimentos, usuários e logs existentes no momento da cópia. Ele também contém dados pessoais e hashes de senha, portanto é **confidencial**. Não envie backups ao GitHub ou a canais públicos.

Adote uma frequência de cópias definida pela instituição e mantenha mais de uma geração, de preferência em locais protegidos distintos. A aplicação não implementa automaticamente uma política externa de retenção ou de backup programado.

### 7. Restauração por upload

**Advertência:** restaurar um backup substitui o banco atual. Dados e logs produzidos depois do backup selecionado podem ser perdidos.

1. Programe uma janela de manutenção e interrompa os atendimentos.
2. Faça e baixe um backup **atual** antes de qualquer restauração.
3. Na aba **Restaurar backup**, envie um arquivo `.zip` de backup do PrestServ.
4. Verifique o arquivo apresentado e marque a confirmação da substituição.
5. Execute **Restaurar banco de dados** somente quando não houver usuários realizando operações.
6. Entre novamente e confira pessoas, usuários, fotos, atendimentos e logs.

O programa verifica formato, estrutura e integridade antes da substituição. O procedimento de restauração foi testado em banco isolado durante a preparação da V1.1.0; **a validação de uma restauração em produção exige cuidados adicionais com sessões e acesso simultâneo**.

A restauração registra um evento no histórico resultante, mas **não preserva os logs gerados após a data do backup restaurado**.

### 8. Proteção de dados e segurança

- Restrinja o acesso à máquina, à pasta do banco e aos arquivos ZIP de backup.
- Use credenciais individuais; desative contas de quem não deve mais acessar.
- Evite compartilhar capturas de tela, CSV ou PDF com dados de pessoas atendidas.
- Não armazene backups nem bancos reais em repositórios públicos.
- O SQLite padrão **não protege o arquivo com senha**; o login restringe o acesso pela aplicação, e não por acesso direto ao disco.
- A auditoria auxilia na rastreabilidade, mas não substitui controles de segurança no sistema operacional, na rede e na infraestrutura.

### 9. Verificações rotineiras

Antes do expediente, confirme o funcionamento da aplicação e o acesso das contas autorizadas. Ao final do dia, revise os atendimentos e faça o backup conforme a política da instituição. Periodicamente, analise os logs, revise contas inativas e confira a qualidade dos cadastros.

### 10. Limitações conhecidas

A V1.1.0 não deve ser descrita como possuidora de **auditoria imutável**, **criptografia nativa do banco SQLite**, **backup automático programado** ou **recuperação automática de dados excluídos**. Essas capacidades exigem soluções específicas que não fazem parte desta atualização.


\newpage

## Instalação e manutenção técnica

### 1. Arquitetura e funcionamento

O PrestServ utiliza **Python**, **Streamlit** (interface web), **SQLite** (persistência), **Pillow** (tratamento de fotografias), **pandas** (consultas e tabelas) e **ReportLab** (relatórios em PDF). Pode ser executado diretamente em ambiente Python ou em contêiner Docker. Na implantação atualmente utilizada, o serviço é acessado por um proxy reverso Nginx.

Existem dois perfis de usuário: `admin` e `porteiro`. A aplicação guarda os usuários no banco SQLite; a autenticação pela interface não cifra o arquivo físico.

### 2. Organização dos arquivos

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

### 3. Preparar o ambiente Python

Crie e ative um ambiente virtual na raiz do projeto:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

No Windows PowerShell, a ativação correspondente é `.venv\Scripts\Activate.ps1`.

O `requirements.txt` deve registrar versões verificadas e compatíveis com o **Python da imagem Docker utilizada**. Um arquivo gerado em ambiente Python 3.14 não garante, por si só, instalação compatível em uma imagem Python 3.12; valide a construção do contêiner antes da publicação.

### 4. Inicializar o banco e criar o administrador inicial

Execute:

```bash
python inicializar_banco.py
python criar_admin.py
```

A primeira execução cria as tabelas de pessoas, serviços, presenças, usuários e fotografias, com os serviços iniciais **Jantar**, **Banho** e **Roupas**. `criar_admin.py` configura a conta administrativa inicial. Guarde as credenciais com segurança.

Na execução normal, `app.py` também chama `inicializar_banco()` antes de disponibilizar as telas.

### 5. Migração de esquema na V1.1.0

O módulo `estrutura_v110.py` cria a tabela `logs` e os índices associados, sem apagar os registros existentes. A migração é chamada pela inicialização do banco e define `PRAGMA user_version = 1` na implementação atual.

- **Banco novo:** a tabela de logs é preparada durante a inicialização.
- **Banco V1.0 existente:** a estrutura de auditoria é criada, preservando os cadastros, usuários e atendimentos existentes.
- **Executar novamente:** a migração foi projetada para ser repetida sem recriar a tabela ou descartar os dados existentes.

A migração foi testada com uma cópia isolada do banco, incluindo verificação de integridade. **Isso não representa um mecanismo genérico de migração para todas as versões futuras**: alterações posteriores exigirão validações próprias.

Não altere manualmente o número `user_version` para simular uma migração de produção sem respaldo técnico.

### 6. Executar a aplicação

```bash
python -m streamlit run app.py
```

O Streamlit utiliza normalmente a porta **8501**, salvo configuração em contrário. Controle acesso, firewall e regras do proxy reverso conforme a instalação. O encerramento ou recarregamento de uma sessão pode exigir novo login; atendimentos já salvos permanecem no banco.

Na versão preparada para publicação, os administradores podem acessar **Presenças**, **Cadastros**, **Relatórios**, **Logs do sistema**, **Backup e restauração** e **Administração**; o porteiro acessa a operação de presenças.

### 7. Banco SQLite e integridade

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

### 8. Exclusões e auditoria

A verificação de vínculos antes de excluir pessoas ou usuários é implementada em `estrutura_v110.py` e aplicada novamente no momento da exclusão. Pessoas com fotografias ou atendimentos vinculados não podem ser excluídas por esse fluxo. O último administrador ativo e a própria conta administrativa estão protegidos contra exclusão.

A rotina de limpeza de logs limita a operação a **500 IDs**, valida autorização e registra a exclusão. **Não considere os logs uma auditoria imutável**, pois um administrador autorizado pode excluí-los pela interface.

Os registros de auditoria podem conter informações administrativas e identificadores pessoais. Controle seu acesso e não os publique.

### 9. Backup e restauração

#### 9.1. Gerar backup

O módulo `backup.py` gera em memória uma cópia consistente do SQLite com `sqlite3.conn.backup()`, compactada em ZIP. O nome do arquivo interno é **`prestserv.db`**. O backup inclui pessoas, usuários, fotografias, atendimentos e logs existentes no momento da geração.

A interface administrativa oferece **Preparar backup** e **Baixar backup ZIP**. Não há necessidade de uma pasta persistente de backups no servidor para este procedimento; a política de armazenamento externo é responsabilidade da instituição.

#### 9.2. Restaurar backup

A restauração aceita ZIP no formato previsto e valida arquivo, tabelas obrigatórias, integridade, relações entre tabelas e existência de administrador ativo antes de substituir o banco. A restauração deve ocorrer **sem atendimentos concorrentes** e com backup prévio do estado atual.

Depois da operação, autentique-se novamente e confira cadastros, pessoas, fotografias, atendimentos e logs. Um backup restaurado pode substituir o histórico atual por um histórico mais antigo; a versão nova registra o evento de restauração no banco restaurado.

#### 9.3. Testes realizados na preparação da V1.1.0

- ZIP de backup: verificada a presença de `prestserv.db`.
- Integridade da cópia: `ok` e nenhuma violação de chaves estrangeiras.
- Migração isolada: tabela `logs` recriada, `user_version = 1`, dados preservados.
- Restauração isolada: integridade `ok`, dados preservados e último evento `restaurar_backup`.

Esses resultados foram obtidos em testes locais. Antes da publicação, valide também a imagem Docker e os procedimentos da infraestrutura real.

### 10. Implantação Docker e proxy reverso

A atualização da imagem Docker deve ser executada somente após validar o `requirements.txt` com a versão de Python definida no `Dockerfile` e confirmar a persistência do diretório `dados/` por volume ou montagem equivalente.

Procedimento recomendado:

1. Registrar o estado atual da implantação e obter um backup ZIP íntegro.
2. Construir e testar a nova imagem na branch de desenvolvimento.
3. Verificar a configuração do volume de dados e os parâmetros de rede/proxy.
4. Publicar a tag da versão no repositório e implantar a imagem revisada no Portainer.
5. Verificar login, operações principais, logs, relatórios e backup após a atualização.

**Nunca recrie ou substitua um volume de produção sem garantir a recuperação dos dados.** Esta documentação não pressupõe comandos exatos de Docker Compose ou Portainer, pois dependem dos arquivos reais de implantação.

### 11. Git e proteção de dados

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

### 12. Checklist de validação antes da publicação

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

### 13. Diagnóstico de problemas

**Banco não encontrado:** confira `DB_PATH` em `database.py`, inclusive maiúsculas e minúsculas, e a montagem do volume.

**Login recusado:** confira a conta, senha e situação ativa; nunca edite o hash manualmente.

**Foto não aparece:** confira a existência do registro em `fotos_pessoas` e o formato da imagem.

**Banco bloqueado (`database is locked`):** verifique operações simultâneas, transações longas e conexões abertas. Não sobrescreva o arquivo SQLite em uso.

**Avisos `use_container_width`:** substitua parâmetros antigos por `width="stretch"` ou `width="content"` conforme o componente. Esses ajustes foram realizados no código de desenvolvimento antes da preparação da documentação.

**PDF com texto difícil de ler:** confira configuração de fontes, caracteres acentuados e contraste dos cabeçalhos nos estilos do ReportLab.

### 14. Autoria

Código, documentação e interface desenvolvidos por **Jeronimo Costa Penha**. A instituição usuária deve definir as políticas locais de operação, guarda de dados e acesso aos backups.

