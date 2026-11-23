---
title: "Apresentação do PrestServ"
subtitle: "Visão geral da versão 2.0.0"
author: "Jeronimo Costa Penha"
date: "Novembro de 2026"
lang: pt-BR
---

## 1. Finalidade do sistema

O **PrestServ** é uma aplicação web para auxiliar uma instituição de assistência social no registro de pessoas atendidas, serviços oferecidos, recebimento de entradas (doações e compras), participação de voluntários e elaboração de relatórios. Foi concebido para uma operação diária simples, com níveis de acesso adequados às responsabilidades de cada colaborador.

O sistema utiliza Python e Streamlit, com armazenamento em SQLite. O acesso é realizado por navegador, em computador ou celular, conforme a infraestrutura disponibilizada pela instituição.

## 2. Pessoas atendidas e serviços

Cada pessoa possui cadastro próprio, com nome obrigatório, informações de contato e identificação quando disponíveis, endereço, observações, situação ativa/inativa e fotografia opcional. O cadastro pode registrar a autorização para **refeição no local**, respeitando os controles definidos pela aplicação.

Cada pessoa pode ter **uma presença por dia**. Uma presença admite vários serviços, como jantar, banho e roupas. Na V2, o mesmo serviço pode ter uma **quantidade registrada**, quando aplicável. A quantidade de itens ou serviços distribuídos não deve ser confundida com o número de presenças.

O registro sem nenhum serviço não é mantido como presença. Pessoas inativas permanecem no histórico, mas não devem ser usadas para novos atendimentos sem reativação autorizada.

## 3. Voluntariado

O módulo de voluntários registra nome, telefone opcional, fotografia e situação ativa/inativa. O controle de presença considera **um comparecimento por voluntário e por data**, sem contabilizar horas trabalhadas ou atividades específicas.

Os responsáveis podem consultar cadastros, corrigir registros conforme o perfil, acompanhar o total de dias e emitir relatórios. O ranking considera dias únicos de presença; empates recebem a mesma posição e a numeração é **densa** (por exemplo, 1, 1, 2, 3). Certificados são gerados para quem alcançar as três primeiras posições distintas, inclusive em caso de empate. Um voluntário inativo com histórico pode participar do ranking.

Os certificados são gerados em PDF, em formato A4 paisagem, com espaço para assinatura e sem declaração de horas de trabalho.

## 4. Entradas

A área de **Entradas** permite registrar movimentações de recebimento, incluindo doações e compras, conforme os campos disponíveis na tela. Esse controle é administrativo e distinto do lançamento de serviços prestados em uma presença.

## 5. Perfis de acesso

| Perfil | Responsabilidades principais |
|:--|:--|
| **Superadministrador** | Todos os recursos autorizados: cadastros, atendimentos, voluntariado, relatórios, administração de usuários, logs, backup e restauração. |
| **Administrador** | Operação e correção de datas, cadastros, entradas, relatórios e gestão operacional de voluntários; sem acesso às funções exclusivas do superadministrador. |
| **Secretaria** | Cadastros de pessoas, entradas e cadastro de voluntários; não registra presenças de voluntários. |
| **Porteiro** | Registra e corrige presenças de pessoas e voluntários na data atual; visualiza apenas os dados necessários à identificação. |
| **Consulta** | Visualiza relatórios e estatísticas agregadas autorizadas, sem acesso aos nomes e dados pessoais de voluntários ou pessoas atendidas. |

Os perfis são verificados pela aplicação e pelas operações de acesso ao banco. O menu exibe somente páginas disponíveis ao usuário.

## 6. Navegação e apresentação

Para administradores, as páginas são agrupadas em áreas como **Atendimentos**, **Voluntários** e, quando permitido, **Administração**. O porteiro utiliza uma navegação direta com apenas **Presenças** e **Presenças de voluntários**.

O Streamlit permite selecionar tema **claro**, **escuro** ou **do sistema** no menu de configurações do navegador. A escolha afeta a interface, não o aspecto institucional dos relatórios PDF.

## 7. Relatórios e proteção dos dados

Os relatórios de atendimentos apresentam indicadores, serviços, frequência e histórico conforme a autorização. Os relatórios de voluntários incluem classificação, cadastros e histórico individual para perfis autorizados; o perfil Consulta recebe somente estatísticas agregadas.

As exportações em CSV e PDF podem conter dados pessoais e exigem armazenamento e compartilhamento responsáveis. Os PDFs institucionais utilizam tons de cinza, e os gráficos podem utilizar cores quando pertinente.

As operações relevantes são registradas em logs, mas o histórico **não é imutável**. O SQLite padrão não cifra o arquivo do banco; a segurança depende também do sistema operacional, da rede, dos backups e do controle de acesso aos arquivos.

## 8. Publicação e limites

A versão 2.0.0 está **em preparação para implantação**. Antes da atualização da produção, é necessário validar a migração do banco existente em uma cópia isolada, verificar integridade e permissões, testar a implantação e manter uma cópia de segurança recuperável.

O PrestServ é uma ferramenta administrativa: não substitui os procedimentos de acolhimento, políticas institucionais de proteção de dados ou documentos legalmente exigíveis.

## 9. Créditos

**Desenvolvido por Jeronimo Costa Penha.**
