# Manual do administrador

**PrestServ 1.0 - cadastros, usuários, relatórios e dados**

## 1. Responsabilidades do administrador

O administrador organiza os cadastros e acessos, revisa registros quando necessário, consulta relatórios e mantém cópias de segurança dos dados. O uso dessa conta deve ser restrito às pessoas formalmente autorizadas.

## 2. Cadastro de pessoas

Acesse **Cadastros**. A tela contém áreas para criar e consultar/editar registros.

### 2.1. Novo cadastro

1. Abra **Novo cadastro**.
2. Informe obrigatoriamente o **nome**.
3. Preencha, quando disponíveis, documento, telefone e contato de referência.
4. Adicione fotografia opcional em formato aceito pelo sistema.
5. Salve o cadastro e confira a confirmação.

As imagens são convertidas para JPEG redimensionado antes do armazenamento no banco. A fotografia serve para auxiliar a identificação; não substitui a confirmação por outros meios quando necessária.

### 2.2. Alterar cadastro

1. Abra **Consultar / editar**.
2. Localize a pessoa por nome ou identificador.
3. Revise os dados e salve as alterações.
4. Se necessário, envie uma nova fotografia ou utilize a opção de remover fotografia mediante confirmação.

### 2.3. Desativar e reativar

A desativação retira a pessoa das opções de novos atendimentos, mas **não apaga seu histórico**. Use-a quando apropriado e reative a pessoa se for necessário voltar a atendê-la. Evite criar cadastro duplicado.

## 3. Administração de usuários

Na área **Administração**, o administrador pode criar contas e, conforme os controles disponíveis na versão instalada, editar nome, login, perfil, situação e redefinir senhas.

| Campo | Boa prática |
|:--|:--|
| Nome | Usar identificação reconhecível do funcionário ou colaborador. |
| Login | Manter identificador individual e único. |
| Senha | Fornecer de modo reservado; o sistema armazena apenas o hash. |
| Perfil | Conceder apenas as permissões necessárias. |
| Situação | Desativar quem não precisa mais acessar; evitar apagar históricos. |

Nunca use uma conta compartilhada se for importante identificar qual operador realizou um atendimento. Não é possível recuperar a senha original pelo hash; a solução é **redefini-la**.

## 4. Relatórios

Acesse **Relatórios** e escolha o período. É possível usar atalhos para o mês, semestre e ano ou informar datas personalizadas.

### 4.1. Filtrar informações

O filtro **Pessoa** permite selecionar uma pessoa específica ou todas as pessoas. O intervalo inclui as datas inicial e final.

### 4.2. Indicadores

- **Pessoas distintas:** quantidade de pessoas atendidas no período, independentemente do número de visitas.
- **Presenças:** quantidade de registros pessoa/data no período.
- **Serviços prestados:** quantidade total de serviços associados às presenças.
- **Dias com registros:** quantidade de datas com presenças.
- **Média por dia registrado:** presenças divididas pelos dias com registros.

### 4.3. Relatórios disponíveis

- **Visão geral:** distribuição de serviços e evolução diária/mensal.
- **Frequência:** número de presenças por pessoa e datas de primeira/última presença no intervalo.
- **Histórico:** linhas individuais por atendimento, com os serviços associados.
- **Ausências:** pessoas ativas sem atendimento nos últimos X dias ou sem atendimento anterior até a data de referência.
- **Cadastros:** informação sobre campos preenchidos e disponibilidade de fotografia.

**Interpretação:** uma pessoa com três presenças e sete serviços representa três dias de comparecimento e sete serviços registrados; não são sete visitas.

### 4.4. Exportar

Use os botões de **CSV** nas seções de tabela ou selecione o conteúdo no campo de exportação e clique em **Baixar relatório em PDF**.

O PDF tem aparência institucional, em tons de cinza. Os gráficos podem aparecer na tela; sua inclusão no PDF depende da versão instalada.

**Privacidade:** antes de compartilhar um PDF ou CSV, verifique se o destinatário está autorizado a receber nomes e histórico de pessoas atendidas. Sempre que possível, prefira dados agregados.

## 5. Backup por download

O PrestServ foi planejado para produzir backup **sob demanda, por download**, sem guardar cópias permanentes na pasta do servidor.

1. Entre com uma conta administrativa.
2. Acesse **Backup e restauração** (se a função já estiver habilitada na instalação).
3. Clique em **Preparar backup**.
4. Clique em **Baixar backup**.
5. Guarde o arquivo `.db` em local seguro, preferencialmente fora do computador que executa o sistema.
6. Confirme que o download foi concluído e que o arquivo está acessível.

O backup inclui cadastros, fotografias, atendimentos e contas de usuário. **Ele contém dados pessoais e hashes de senhas; trate-o como informação confidencial.**

Sugestão operacional: realizar o download em uma frequência definida pela instituição, por exemplo após cada dia de atendimento, e guardar mais de uma geração em locais protegidos.

## 6. Restauração por upload

**Advertência:** restaurar um backup substitui os dados existentes pelo conteúdo do arquivo escolhido. Registros criados após a data daquele backup podem ser perdidos.

Procedimento seguro:

1. Planeje uma janela de manutenção e interrompa o uso por todos os operadores.
2. Faça e baixe um backup do estado atual antes da restauração.
3. Na área **Restaurar backup**, selecione o arquivo `.db`.
4. Confira nome e tamanho e confirme conscientemente a substituição.
5. Execute a restauração somente com todas as conexões de atendimento encerradas e com o procedimento técnico de manutenção validado.
6. Reabra o sistema, autentique-se novamente e confira cadastros, fotos e atendimentos de amostra.

**Não faça uma restauração em produção enquanto houver usuários trabalhando.** A presença de um aviso na tela, por si só, não garante que outras sessões foram interrompidas. O mecanismo de bloqueio/manutenção deve ser testado antes de liberar esta função.

## 7. Proteção dos dados

- Restrinja o acesso à máquina e à pasta que contém `prestserv.db`.
- Não envie o banco real, backups ou relatórios pessoais para um repositório público.
- Proteja os arquivos baixados e elimine cópias desnecessárias de forma apropriada.
- Exija credenciais individuais e desative acessos não utilizados.
- Evite abrir o PrestServ em rede pública sem medidas adicionais de proteção.
- O SQLite padrão **não possui senha de acesso ao arquivo**; o login do PrestServ protege a interface, não a leitura direta do arquivo por quem tem permissões no sistema operacional.

## 8. Verificação rotineira

Antes de iniciar as atividades: confirmar acesso dos usuários, data do sistema e disponibilidade da aplicação. Ao final: conferir os lançamentos do dia e executar o procedimento institucional de backup. Periodicamente: revisar cadastros duplicados/inativos, permissões de usuários e qualidade dos dados.

## 9. O que não deve ser presumido nesta versão

A documentação não afirma que exista auditoria imutável de ações, expiração de sessão, backup automático ou criptografia do arquivo SQLite. Essas funções devem ser consideradas **indisponíveis** até serem expressamente implementadas e testadas.
