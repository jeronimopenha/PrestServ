---
title: "Manual do administrador"
subtitle: "PrestServ 1.1.0 — Cadastros, usuários, relatórios, auditoria e dados"
author: "Jeronimo Costa Penha"
date: "Novembro de 2026"
lang: pt-BR
---

## 1. Responsabilidades do administrador

O administrador organiza os cadastros e acessos, revisa atendimentos, acompanha relatórios, consulta o histórico de operações e mantém cópias de segurança. O uso da conta administrativa deve ficar restrito às pessoas autorizadas.

## 2. Cadastro de pessoas

Acesse **Cadastros**, onde estão as áreas **Novo cadastro** e **Consultar / editar**.

### 2.1. Cadastrar

1. Abra **Novo cadastro** e informe obrigatoriamente o **nome**.
2. Preencha, quando disponíveis, documento, telefone e contato de referência.
3. Acrescente uma fotografia opcional, nos formatos aceitos pela interface.
4. Salve e confira a confirmação.

As fotos são convertidas para JPEG e redimensionadas antes de serem armazenadas no banco. A imagem auxilia a identificação, mas não substitui a conferência de outros dados quando necessário.

### 2.2. Editar, fotografar e desativar

1. Abra **Consultar / editar** e selecione a pessoa.
2. Altere os dados necessários e salve.
3. Se for o caso, substitua ou remova a fotografia, observando a confirmação exigida na interface.
4. Use **Desativar pessoa** para impedir novos atendimentos sem perder o histórico; **Reativar pessoa** permite voltar a registrar atendimentos.

### 2.3. Exclusão condicionada (V1.1.0)

A exclusão definitiva só é disponibilizada quando não há relacionamentos que a impeçam. A verificação considera, entre outros, registros de **presença** e **fotografia**. Uma pessoa que possui apenas fotografia também não pode ser excluída enquanto a foto não for removida.

- Se houver histórico de atendimentos, prefira **desativar**: o sistema preserva os registros anteriores.
- Se a pessoa não tiver vínculos impeditivos, o administrador poderá solicitar a exclusão e confirmar a operação.
- A verificação é realizada novamente ao excluir, para evitar inconsistências caso os dados tenham mudado.

**Atenção:** exclusão é permanente. A existência de um log da operação não permite recuperar automaticamente o registro excluído.

## 3. Administração de usuários

Na área **Administração**, o administrador pode criar usuários, editar nome, login e perfil, ativar/desativar contas e redefinir senhas.

| Campo | Boa prática |
|:--|:--|
| Nome | Identificação reconhecível do colaborador. |
| Login | Identificador individual e único. |
| Senha | Entregar reservadamente; o sistema armazena o hash, não a senha original. |
| Perfil | Conceder apenas as permissões necessárias (`admin` ou `porteiro`). |
| Situação | Desativar contas sem uso, preservando o histórico operacional. |

### 3.1. Exclusão de usuários (V1.1.0)

É possível excluir contas sem vínculos operacionais que impeçam a operação. O sistema aplica proteções adicionais:

- Um administrador não pode excluir a própria conta.
- Não é permitido excluir ou deixar indisponível o último administrador ativo.
- O usuário precisa ter permissão administrativa ativa.
- A exclusão exige confirmação.

Os registros de auditoria guardam o login e o identificador do operador sem criar vínculo de chave estrangeira com a tabela de usuários. Por isso, **logs antigos, por si só, não bloqueiam a exclusão de uma conta**. Eles podem continuar mostrando o login de um usuário já removido.

Não compartilhe contas: os logs dependem da identificação individual. Senhas esquecidas devem ser **redefinidas**, e não recuperadas a partir do hash.

## 4. Relatórios

Acesse **Relatórios**, escolha o período (**Mês atual**, **Semestre atual**, **Ano atual** ou **Personalizado**) e, se necessário, selecione uma pessoa. As datas inicial e final integram o intervalo consultado.

### 4.1. Indicadores

- **Pessoas distintas:** pessoas diferentes atendidas no período.
- **Presenças:** registros únicos de pessoa e data.
- **Serviços prestados:** quantidade total de serviços associados às presenças.
- **Dias com registros:** quantidade de datas com ao menos uma presença.
- **Média por dia registrado:** presenças divididas pela quantidade de dias registrados.

Por exemplo, três presenças e sete serviços representam **três dias de comparecimento** e **sete serviços prestados**, não sete visitas.

### 4.2. Consultas e exportação

- **Visão geral:** distribuição de serviços e evolução dos registros.
- **Frequência:** quantidade de presenças por pessoa.
- **Histórico:** atendimentos individuais e respectivos serviços.
- **Ausências:** pessoas ativas sem atendimento recente.
- **Cadastros:** preenchimento de campos e disponibilidade de fotografia.

As tabelas podem oferecer exportação em **CSV**; a tela também permite gerar relatórios em **PDF**, com apresentação institucional em tons de cinza. Antes de compartilhar arquivos, confira se os destinatários estão autorizados a acessar os dados pessoais.

## 5. Logs do sistema (V1.1.0)

Acesse **Logs do sistema** no menu administrativo para consultar eventos de autenticação, cadastros, atendimentos, fotografias, usuários, backups, restaurações e outras operações auditadas.

### 5.1. Consultar

1. Se necessário, filtre por **operador**, **ação**, **resultado** e **período**.
2. Ajuste o **máximo de registros** exibidos.
3. Consulte a tabela ordenada pelas operações registradas.
4. Na seção **Detalhes da operação**, selecione o ID de um registro para examinar as informações adicionais.

O filtro de **ação** apresenta as ações encontradas no histórico. As datas exibidas na interface são convertidas para o horário de Brasília; o banco armazena os horários de auditoria em UTC.

### 5.2. Limpar logs selecionados

1. Marque as caixas de seleção dos registros que deseja excluir, ou utilize **Selecionar todos** para selecionar os exibidos.
2. Confira a quantidade selecionada; o limite é de **500 registros por operação**.
3. Marque a confirmação de exclusão definitiva.
4. Clique em **Excluir selecionados**.

A exclusão gera um **novo log `excluir_logs`**, contendo o operador, a quantidade e os identificadores removidos. A operação de limpeza não restaura os eventos apagados.

**Limitação:** a trilha de auditoria não é imutável. Um administrador poderá excluir posteriormente até mesmo o registro de uma limpeza anterior. A exclusão não deve ser tratada como um mecanismo de retenção inviolável.

## 6. Backup por download

Na área **Backup e restauração**, abra a aba de backup:

1. Clique em **Preparar backup**.
2. Clique em **Baixar backup ZIP**.
3. Salve o arquivo `.zip` em local seguro, preferencialmente fora do computador do servidor.
4. Confira o arquivo obtido antes de considerá-lo uma cópia de segurança válida.

O ZIP contém o arquivo **`prestserv.db`**, que inclui cadastros, fotos, atendimentos, usuários e logs existentes no momento da cópia. Ele também contém dados pessoais e hashes de senha, portanto é **confidencial**. Não envie backups ao GitHub ou a canais públicos.

Adote uma frequência de cópias definida pela instituição e mantenha mais de uma geração, de preferência em locais protegidos distintos. A aplicação não implementa automaticamente uma política externa de retenção ou de backup programado.

## 7. Restauração por upload

**Advertência:** restaurar um backup substitui o banco atual. Dados e logs produzidos depois do backup selecionado podem ser perdidos.

1. Programe uma janela de manutenção e interrompa os atendimentos.
2. Faça e baixe um backup **atual** antes de qualquer restauração.
3. Na aba **Restaurar backup**, envie um arquivo `.zip` de backup do PrestServ.
4. Verifique o arquivo apresentado e marque a confirmação da substituição.
5. Execute **Restaurar banco de dados** somente quando não houver usuários realizando operações.
6. Entre novamente e confira pessoas, usuários, fotos, atendimentos e logs.

O programa verifica formato, estrutura e integridade antes da substituição. O procedimento de restauração foi testado em banco isolado durante a preparação da V1.1.0; **a validação de uma restauração em produção exige cuidados adicionais com sessões e acesso simultâneo**.

A restauração registra um evento no histórico resultante, mas **não preserva os logs gerados após a data do backup restaurado**.

## 8. Proteção de dados e segurança

- Restrinja o acesso à máquina, à pasta do banco e aos arquivos ZIP de backup.
- Use credenciais individuais; desative contas de quem não deve mais acessar.
- Evite compartilhar capturas de tela, CSV ou PDF com dados de pessoas atendidas.
- Não armazene backups nem bancos reais em repositórios públicos.
- O SQLite padrão **não protege o arquivo com senha**; o login restringe o acesso pela aplicação, e não por acesso direto ao disco.
- A auditoria auxilia na rastreabilidade, mas não substitui controles de segurança no sistema operacional, na rede e na infraestrutura.

## 9. Verificações rotineiras

Antes do expediente, confirme o funcionamento da aplicação e o acesso das contas autorizadas. Ao final do dia, revise os atendimentos e faça o backup conforme a política da instituição. Periodicamente, analise os logs, revise contas inativas e confira a qualidade dos cadastros.

## 10. Limitações conhecidas

A V1.1.0 não deve ser descrita como possuidora de **auditoria imutável**, **criptografia nativa do banco SQLite**, **backup automático programado** ou **recuperação automática de dados excluídos**. Essas capacidades exigem soluções específicas que não fazem parte desta atualização.
