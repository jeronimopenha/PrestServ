---
title: "Manual do administrador"
subtitle: "PrestServ 2.0.0 - operações, relatórios e administração"
author: "Jeronimo Costa Penha"
date: "Novembro de 2026"
lang: pt-BR
---

## 1. Perfis administrativos

Na V2.0.0, **Administrador** (`admin`) e **Superadministrador** (`superadmin`) são perfis distintos. Ambos atuam na operação do atendimento e do voluntariado, com acesso a cadastros, entradas e relatórios autorizados. **Somente o superadministrador** gerencia usuários, consulta/limpa logs e executa backup ou restauração pela interface.

Cada usuário deve acessar com sua própria conta. O menu organiza as páginas em **Atendimentos**, **Voluntários** e, conforme as permissões, **Administração**.

## 2. Pessoas atendidas

### 2.1. Criar e manter cadastros

Em **Atendimentos > Cadastros**, utilize as áreas de novo cadastro e consulta/edição. Registre nome obrigatório e, quando disponíveis, documento, telefone, pessoa de contato, endereço, observações e fotografia. Verifique os dados antes de salvar e evite cadastros duplicados.

O cadastro também contém a indicação de **autorização para refeição no local**. A equipe deve obedecer às regras institucionais ao definir essa condição. Fotografias e observações são dados pessoais e exigem controle de acesso.

### 2.2. Status e exclusão

A **desativação** impede novos registros operacionais sem apagar o histórico existente; a **reativação** permite o retorno às operações autorizadas.

A exclusão definitiva é condicionada à inexistência de vínculos impeditivos, como presenças e fotografias, e exige confirmação. Registros com histórico devem ser preservados por desativação, em vez de exclusão. O sistema verifica os vínculos novamente no momento da operação.

## 3. Presenças e quantidades de serviços

Em **Atendimentos > Presenças**, selecione a pessoa, confirme a data e marque os serviços efetivamente prestados. Na V2, cada serviço pode ter uma **quantidade**. Uma pessoa possui apenas **uma presença por data**, mesmo que sejam registrados diferentes serviços ou várias unidades de um serviço.

Administradores autorizados podem selecionar datas anteriores para corrigir lançamentos; a interface impede datas futuras. O porteiro trabalha somente no dia atual. Quando não resta nenhum serviço associado, o sistema remove a presença, seguindo as confirmações aplicáveis.

Ao analisar relatórios, não confunda quantidade de serviços, unidades distribuídas e presenças distintas.

## 4. Entradas de doações e compras

Acesse **Atendimentos > Entradas** para registrar entradas recebidas. Selecione o tipo de lançamento e preencha os campos disponíveis, conferindo datas e informações antes de salvar. Não trate entradas como evidência automática de distribuição ao público; os serviços entregues são registrados em presenças.

O perfil Secretaria também pode operar essa área. O porteiro e o perfil Consulta não realizam lançamentos de entradas.

## 5. Voluntários

### 5.1. Cadastros

Em **Voluntários > Cadastro de voluntários**, registre nome, telefone opcional, fotografia e situação ativo/inativo. A desativação mantém o histórico. A exclusão definitiva é uma função restrita e condicionada à ausência de vínculos impeditivos; caso exista histórico, prefira desativar o cadastro.

### 5.2. Presenças

Em **Voluntários > Presenças de voluntários**, registre e consulte os comparecimentos. O PrestServ aceita **um comparecimento por voluntário/dia**, sem controle de horas e sem associação de atividades. O porteiro pode registrar/remover presenças apenas na data atual; administradores autorizados podem corrigir outras datas permitidas.

### 5.3. Ranking, relatórios e certificados

Em **Voluntários > Relatórios de voluntários**, os perfis autorizados podem consultar ranking por dias de presença, lista de cadastros (inclusive sem presença e inativos) e histórico de voluntário, além de exportações CSV e PDF.

O ranking usa **posições densas**: em caso de empate, ambos os voluntários recebem a mesma posição, e a posição seguinte aumenta em uma unidade (por exemplo, 1, 1, 2, 3). O certificado é disponibilizado para **todos os colocados nas três primeiras posições distintas**, mesmo que haja mais de três pessoas por causa de empates. Voluntários inativos com presenças no período continuam elegíveis. Os certificados são A4 paisagem, sem declaração de horas e com campo para assinatura.

A exportação de relatórios e certificados é auditada. Confira período, dados e destinatários antes de distribuir os arquivos.

## 6. Relatórios de atendimentos

Em **Atendimentos > Relatórios**, escolha um período, visualize indicadores, serviços prestados, quantidades distribuídas, frequência, evolução temporal e outras consultas permitidas. Conforme o perfil, há histórico individual, filtros e exportações CSV/PDF.

Indicadores usuais:

| Indicador | Interpretação |
|:--|:--|
| Pessoas distintas | Pessoas diferentes atendidas no período. |
| Presenças | Combinações únicas de pessoa e dia. |
| Serviços registrados | Ocorrências de tipos de serviços em presenças. |
| Unidades distribuídas | Soma das quantidades informadas para os serviços. |
| Dias com registros | Dias com ao menos uma presença, não necessariamente dias de funcionamento. |

As exportações com nomes, contatos ou histórico individual são restritas aos perfis autorizados. O perfil Consulta vê somente agregados.

## 7. Funções exclusivas do superadministrador

### 7.1. Administração de usuários

Em **Administração**, o superadministrador pode criar e editar usuários, alterar perfil e situação, redefinir senhas e solicitar exclusões condicionadas.

Os cinco perfis são `superadmin`, `admin`, `secretaria`, `porteiro` e `consulta`. Atribua a cada colaborador o menor conjunto de permissões necessário. Não compartilhe senhas nem tente recuperar senhas a partir de seus hashes.

O sistema impede operações inseguras, como excluir a própria conta ou deixar a aplicação sem um superadministrador ativo, e verifica vínculos operacionais antes de exclusões definitivas.

### 7.2. Logs e auditoria

Em **Logs do sistema**, o superadministrador consulta registros de autenticação e outras operações relevantes, com filtros e detalhes. Os horários registrados em UTC são convertidos para o fuso de Brasília na interface.

A exclusão de logs é restrita, exige confirmação e possui limite operacional por seleção. O próprio evento de limpeza é auditado. **Os logs não são imutáveis**: um superadministrador autorizado pode eliminar registros, e restaurar um backup antigo pode substituir todo o histórico posterior àquele backup.

### 7.3. Backup e restauração

Em **Backup e restauração**, o superadministrador pode preparar e baixar um ZIP contendo o banco SQLite completo, inclusive dados de voluntários, fotografias, usuários, entradas e logs.

Para restaurar, interrompa os atendimentos, gere e guarde um backup recente, selecione o ZIP, confirme a substituição e execute a operação somente durante janela de manutenção. A aplicação valida a estrutura e integridade antes da substituição; ao final, reautentique e confira os registros recuperados.

**Cuidado:** restaurar um backup antigo pode apagar alterações realizadas desde a geração desse arquivo. Não há reversão automática.

## 8. Proteção de dados e rotinas de conferência

- Utilize contas individuais e desative acessos de colaboradores desligados.
- Restrinja fotos, contatos, observações, CSV, PDF e ZIP às pessoas legitimamente autorizadas.
- Guarde backups em local protegido e fora da máquina principal, com política de retenção institucional.
- Revise cadastros, correções retroativas, registros de entradas e presença de voluntários.
- Confira a integridade dos dados e a capacidade de restauração periodicamente.

O login do PrestServ não cifra o arquivo SQLite no disco. Controles de armazenamento, rede, sistema operacional e acesso físico continuam necessários.

## 9. Limitações conhecidas

A V2.0.0 não deve ser apresentada como solução com **auditoria imutável**, **criptografia nativa do SQLite**, **backup automático programado** ou **recuperação automática de dados excluídos**. A existência de certificados de voluntariado não significa controle de carga horária.

A documentação descreve funcionalidades implementadas no ambiente de desenvolvimento e ainda sujeitas à validação de implantação.
