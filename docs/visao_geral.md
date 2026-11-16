---
title: "Apresentação do PrestServ"
subtitle: "Finalidade: registro e acompanhamento de atendimentos sociais"
author: "Jeronimo Costa Penha"
date: "Novembro de 2026"
lang: pt-BR
---


## 1. O que é o PrestServ

O **PrestServ** é uma aplicação de apoio ao registro de atendimentos de uma instituição de assistência social. Ela permite identificar as pessoas cadastradas, registrar os serviços recebidos em determinada data e consultar informações consolidadas sobre os atendimentos realizados.

O sistema foi concebido para uma operação simples, com poucos usuários, evitando burocracia desnecessária durante o atendimento.

**Exemplos de serviços:** jantar, banho e roupas. Os serviços efetivamente disponíveis dependem do cadastro de serviços do banco de dados.

## 2. O que o sistema registra

- **Pessoas:** identificação, documento (quando informado), telefones, contato de referência, situação ativa/inativa e fotografia opcional.
- **Atendimentos:** pessoa, data do atendimento e serviços recebidos.
- **Usuários:** nome, login, perfil, situação ativa/inativa e senha armazenada em forma de hash.
- **Relatórios:** indicadores, frequência, serviços prestados e histórico de atendimentos.
- **Auditoria (V1.1.0):** data e hora das operações, identificação do operador, ação, resultado e detalhes quando disponíveis.

Uma pessoa pode receber vários serviços no mesmo dia, mas terá **uma única presença por data**. Por exemplo, jantar e banho no mesmo dia correspondem a uma presença e dois serviços. Um atendimento sem serviços selecionados não é mantido no banco.

## 3. Perfis de acesso

| Perfil | Atividades principais |
|:--|:--|
| **Porteiro** | Localizar pessoa cadastrada, conferir identificação e registrar ou corrigir serviços na data selecionada. |
| **Administrador** | Todas as atividades do porteiro, além de cadastro de pessoas, gestão de usuários, relatórios, consulta de logs, backup e restauração. |

A aplicação não disponibiliza cadastro público de pessoas nem acesso anônimo ao histórico.

## 4. Como o sistema funciona

1. O administrador cria o cadastro inicial da pessoa, preferencialmente com fotografia.
2. O porteiro seleciona a data e localiza a pessoa na lista pesquisável.
3. O porteiro confere os dados e marca os serviços recebidos.
4. Ao salvar, o sistema registra ou atualiza a presença daquela pessoa naquela data.
5. O administrador acompanha os resultados nos relatórios e pode exportá-los.

Caso uma pessoa ainda não esteja cadastrada, o procedimento operacional previsto é anotar o atendimento para posterior cadastro pelo administrador. O porteiro não deve usar o cadastro de outra pessoa para registrar esse atendimento.

## 5. Conceitos dos relatórios

| Indicador | Significado |
|:--|:--|
| **Pessoas distintas** | Número de pessoas diferentes com presença no período. |
| **Presenças** | Número de combinações pessoa + data registradas. |
| **Serviços prestados** | Soma das associações entre presenças e serviços. |
| **Dias com registros** | Datas em que existe ao menos uma presença. |
| **Média por dia registrado** | Presenças divididas pelos dias com registros; não necessariamente dias de funcionamento. |

**Atenção:** não se deve interpretar ausência de registros em uma data como prova de que a instituição funcionou naquele dia e não recebeu ninguém.

## 6. Limites e boas práticas

O PrestServ é um instrumento administrativo, e não substitui políticas institucionais de proteção de dados, procedimentos de acolhimento ou registros obrigatórios de outras áreas. Fotografias, contatos e históricos são dados pessoais: devem ser visualizados apenas por pessoas autorizadas.

O banco SQLite padrão não exige senha para abrir o arquivo diretamente. Por isso, a proteção do computador, as permissões de acesso ao arquivo e o armazenamento seguro de backups são fundamentais.

## 7. Auditoria e exclusão (V1.1.0)

As operações relevantes são registradas para facilitar a identificação de alterações. Somente administradores podem consultar e excluir logs pela interface. A exclusão de pessoas e usuários é condicionada aos vínculos existentes; quando um cadastro possui histórico associado, a desativação permite preservá-lo.

**Limite importante:** logs podem ser excluídos por administradores e não constituem trilha de auditoria imutável. Um backup restaurado não preserva automaticamente operações realizadas após a criação desse backup.

## 8. Créditos

**Desenvolvido por Jeronimo Costa Penha.**  
PrestServ - documentação da versão 1.1.0.
