---
title: "Manual completo do PrestServ"
subtitle: "Versão 2.0.0 - operação, administração e manutenção"
author: "Jeronimo Costa Penha"
date: "Novembro de 2026"
lang: pt-BR
---

\newpage

# Apresentação do PrestServ

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

\newpage

# Manual do porteiro

## 1. Entrar e navegar

1. Abra o endereço do PrestServ informado pela instituição em computador ou celular autorizado.
2. Entre com seu **login** e **senha** pessoais.
3. Na barra lateral, utilize **Presenças** ou **Presenças de voluntários**. A opção **Documentação** permite consultar os manuais disponíveis para seu perfil.
4. Ao terminar o turno, clique em **Sair**.

Não compartilhe credenciais. O recarregamento da página pode exigir nova autenticação; um registro efetivamente salvo permanece no banco.

## 2. Registrar a presença de uma pessoa atendida

1. Abra **Presenças** e confira a data exibida. **O porteiro só opera na data atual**: a alteração da data fica bloqueada.
2. Selecione a pessoa pelo nome e confira os elementos disponíveis de identificação, incluindo a fotografia, se houver.
3. Marque os serviços efetivamente fornecidos, como jantar, banho e roupas.
4. Quando um serviço possuir campo de quantidade, informe a quantidade efetiva de unidades ou atendimentos daquele serviço.
5. Salve o registro e confira a confirmação da aplicação.

Existe **uma única presença por pessoa e por dia**, mesmo que ela receba vários serviços. A soma das quantidades dos serviços não representa o número de pessoas presentes.

## 3. Corrigir um atendimento do dia

1. Na tela **Presenças**, localize a pessoa já atendida.
2. Confira os serviços e as quantidades registrados para a data atual.
3. Faça as correções necessárias e salve novamente.

Se todos os serviços forem retirados, o sistema poderá remover a presença correspondente, conforme o fluxo de confirmação. Verifique com atenção antes de confirmar a remoção.

**Atendimentos de dias anteriores:** solicite o lançamento ou a correção a um administrador autorizado. Não registre uma ocorrência antiga com a data de hoje para contornar essa restrição.

## 4. Refeição no local

O cadastro pode indicar se a pessoa está autorizada a receber **refeição no local**. Observe os avisos e bloqueios apresentados pelo PrestServ. O porteiro não deve alterar um cadastro ou contornar uma restrição de atendimento: encaminhe a situação à secretaria ou à administração.

## 5. Registrar presença de voluntários

1. Abra **Presenças de voluntários**.
2. Selecione um voluntário **ativo**, verificando o nome e, quando houver, a foto.
3. Registre a presença para a data atual e confira a confirmação.
4. Consulte a relação de voluntários presentes no dia para evitar lançamentos repetidos.

Cada voluntário pode possuir **uma presença por dia**. O registro não contabiliza horas nem atividades. Se uma presença do dia tiver sido lançada incorretamente, utilize a ação de remoção disponível na tela e confirme com cuidado.

O porteiro não cadastra voluntários, não altera seu status e não corrige datas anteriores. Esses procedimentos devem ser encaminhados ao pessoal autorizado.

## 6. Pessoa ou voluntário não localizado

Verifique a grafia e a seleção. Cadastros inativos podem não aparecer entre as opções de registro. Nunca registre uma presença em nome de outra pessoa. Avise a secretaria ou a administração, que poderá verificar o cadastro e, se permitido, regularizar a situação.

## 7. Proteção de dados e boas práticas

- Use somente sua conta, mantenha a tela protegida e faça logout ao finalizar.
- Confira a identidade antes de salvar, especialmente em caso de nomes semelhantes.
- Não compartilhe fotos, capturas de tela, dados de contato ou histórico de atendimentos.
- Em caso de falha de conexão, confirme se o lançamento foi salvo antes de repetir a operação.
- Em dúvida sobre presença antiga, cadastro ou autorização de refeição, procure a administração.

## 8. Dúvidas frequentes

**Posso registrar um atendimento de ontem?** Não. O porteiro trabalha apenas na data atual. Solicite a correção ao administrador.

**A mesma pessoa pode receber banho e jantar?** Sim. Registre os serviços recebidos e suas quantidades, quando aplicável, na mesma presença diária.

**Posso registrar a presença do mesmo voluntário duas vezes no dia?** Não. O banco mantém apenas uma presença por voluntário e data.

**Posso cadastrar pessoas ou voluntários?** Não com o perfil de porteiro. Solicite à secretaria ou ao responsável autorizado.

**Posso consultar relatórios?** Não pelo perfil de porteiro. Utilize apenas as telas operacionais permitidas.

## 9. Roteiro rápido

**Pessoas:** data de hoje -> pessoa correta -> conferir identificação -> serviços e quantidades -> salvar -> confirmar.  
**Voluntários:** data de hoje -> voluntário correto -> registrar presença -> conferir na lista do dia.

\newpage

# Manual da secretaria

## 1. Acesso e atividades

Entre no PrestServ com seu login individual. O perfil **Secretaria** trabalha principalmente com **Cadastros**, **Entradas** e **Cadastro de voluntários**, organizados pelas áreas da navegação.

Esse perfil não registra presenças de pessoas ou voluntários, não acessa dados administrativos de usuários, não gerencia backups e não consulta logs do sistema.

## 2. Cadastro de pessoas atendidas

Em **Atendimentos > Cadastros**, utilize **Novo cadastro** ou **Consultar / editar**. Informe o nome e, quando disponíveis, documento, telefones, contato de referência, endereço e observações pertinentes ao atendimento. A fotografia é opcional e auxilia a identificação.

O cadastro possui indicação relacionada à **autorização de refeição no local**. Preencha ou altere essa informação somente conforme a orientação e os critérios da instituição; não a utilize como substituta de uma avaliação de atendimento.

Revise os dados antes de salvar. Evite cadastros duplicados: pesquise o nome antes de criar novo registro. Para deixar de oferecer novos atendimentos sem apagar o histórico, utilize a opção de **desativação**, quando aplicável.

A exclusão definitiva de pessoas não faz parte das permissões do perfil Secretaria. Solicite avaliação de administrador autorizado quando necessário.

## 3. Entradas: doações e compras

Em **Atendimentos > Entradas**, registre as entradas recebidas pela instituição, distinguindo doações e compras segundo os campos disponibilizados pelo sistema. Confira data, tipo e demais informações antes de confirmar.

A área Entradas não representa, por si só, distribuição ao público: os serviços prestados são registrados nas presenças pelos operadores autorizados.

## 4. Cadastro de voluntários

Em **Voluntários > Cadastro de voluntários**, é possível cadastrar e editar voluntários, incluindo nome obrigatório, telefone opcional, fotografia e situação **ativo/inativo**.

A desativação conserva o histórico de presenças. Voluntários inativos não devem ser oferecidos para novos registros operacionais. A Secretaria pode atualizar cadastros, mas **não registra, corrige ou remove presenças** de voluntários; essa tarefa pertence aos perfis autorizados.

A exclusão definitiva de voluntários também é restrita a perfis superiores, condicionada à inexistência de histórico impeditivo.

## 5. Privacidade e cuidados

Fotografias, telefones, contatos de referência, endereços e observações são dados pessoais. Consulte somente os registros necessários ao trabalho, evite compartilhamentos não autorizados e não armazene cópias fora dos locais aprovados pela instituição.

Use credenciais individuais e o comando **Sair** ao encerrar o expediente. Em caso de inconsistência histórica ou necessidade de intervenção em data passada, comunique a administração.

\newpage

# Manual do perfil Consulta

## 1. Finalidade do perfil

O perfil **Consulta** acompanha resultados gerais da instituição sem executar cadastros, lançamentos ou alterações. Ele dispõe das páginas **Relatórios** e **Relatórios de voluntários** em suas respectivas áreas de navegação.

As informações exibidas para esse perfil são **agregadas**. Não é permitido consultar nomes, fotografias, telefones ou histórico individual de pessoas atendidas ou voluntários.

## 2. Relatórios de atendimentos

Abra **Relatórios** e selecione o período disponível. Observe indicadores como total de presenças, pessoas distintas, serviços, unidades e evolução temporal, conforme apresentado pela interface.

**Presença** é uma pessoa em determinado dia. **Unidades distribuídas** representam as quantidades dos serviços; portanto, um total de unidades maior que o de presenças não é inconsistência.

Não interprete automaticamente um dia sem registros como um dia em que a instituição funcionou sem atendimentos: pode não haver expediente, ou os registros podem estar incompletos.

## 3. Estatísticas de voluntários

Abra **Relatórios de voluntários** para observar somente os indicadores gerais disponibilizados. O perfil Consulta não visualiza ranking nominal, contatos, fotografias, cadastros individuais, histórico pessoal, nem utiliza as exportações restritas dos administradores.

As estatísticas se baseiam em registros diários, não em horas trabalhadas.

## 4. Cuidados na interpretação

Compare períodos equivalentes quando possível. Diferencie os conceitos de **pessoa distinta**, **presença**, **serviço registrado** e **quantidade distribuída**. A ausência de um dado não comprova ausência de atendimento.

Os indicadores servem ao acompanhamento administrativo e não substituem a conferência dos registros na fonte pelos responsáveis autorizados.

## 5. Segurança

Não compartilhe credenciais nem tente obter dados de identificação por outros meios. Utilize **Sair** ao concluir a consulta. Solicitações de relatórios individualizados deverão ser encaminhadas aos responsáveis autorizados, respeitando as regras institucionais de proteção de dados.

\newpage

# Manual do administrador

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

\newpage

# Instalação e manutenção técnica

## 1. Arquitetura e estado da versão

O PrestServ utiliza **Python**, **Streamlit**, **SQLite**, **Pillow**, **pandas** e **ReportLab**. A implantação institucional conhecida usa **Docker** para executar a aplicação e **Nginx** como proxy reverso, com persistência do banco por volume ou montagem do diretório de dados.

A **V2.0.0 é candidata à publicação**. A documentação não confirma que o contêiner, o Nginx ou o banco de produção já tenham sido atualizados. Não inicie a V2 sobre um banco antigo sem executar e validar a migração.

## 2. Organização do projeto

A organização abaixo reflete a **reorganização de módulos confirmada pelo desenvolvedor** antes da publicação. Os caminhos devem ser conferidos no repositório definitivo caso outras alterações tenham sido feitas após essa reorganização.

```text
PrestServ/
├── app.py                         # Entrada da aplicação Streamlit
├── README.md
├── LICENSE
├── requirements.txt
├── .streamlit/
│   └── config.toml                # Temas claro e escuro
├── .vscode/
│   └── launch.json                # Ambiente de desenvolvimento local
├── bd_schemes/                   # Esquema e migrações SQLite
│   ├── estrutura_v110.py
│   ├── estrutura_v200.py
│   ├── estrutura_entradas.py
│   ├── estrutura_voluntarios.py
│   └── inicializar_banco.py
├── conn/
│   └── database.py                # Conexões e acesso aos dados
├── security/
│   ├── auth.py                    # Autenticação e usuários
│   └── permissoes.py              # Regras de autorização
├── common/
│   └── config.py                  # Constantes da aplicação
├── model/                         # Regras de negócio e consultas
│   ├── consultas_relatorios.py
│   ├── consultas_voluntarios.py
│   ├── entradas.py
│   ├── fotos.py
│   └── voluntarios.py
├── services/                      # Backups e documentos gerados
│   ├── backup.py
│   ├── pdf_relatorios.py
│   ├── pdf_voluntarios.py
│   └── certificados_voluntarios.py
├── telas/                         # Interface e navegação
│   ├── tela_backups.py
│   ├── tela_cadastros.py
│   ├── tela_cadastros_voluntarios.py
│   ├── tela_documentacao.py
│   ├── tela_entradas.py
│   ├── tela_logs.py
│   ├── tela_presencas.py
│   ├── tela_presencas_voluntarios.py
│   ├── tela_relatorios.py
│   └── tela_relatorios_voluntarios.py
├── scripts/                       # Ferramentas administrativas
│   ├── criar_admin.py
│   └── migrar_prestserv_v200.py
├── docs/                          # Documentação e PDFs distribuídos
│   ├── README.md
│   ├── visao_geral.md
│   ├── manual_porteiro.md
│   ├── manual_secretaria.md
│   ├── manual_consulta.md
│   ├── manual_administrador.md
│   ├── instalacao_manutencao.md
│   ├── manual_completo.md
│   ├── estilo_pdf.tex
│   └── gerar_manuais.sh
└── dados/                         # Banco persistente; fora do Git
    └── PrestServ.db
```

As pastas Python usadas como pacotes podem conter arquivos `__init__.py` não representados na árvore. A pasta `dados/` e outros arquivos locais confidenciais **não devem ser versionados nem incluídos na imagem Docker**.

A camada de acesso ao banco permanece centralizada em `conn/database.py`; reorganizar fisicamente os arquivos não altera, por si só, a lógica de autorização ou de migração. Os PDFs dos manuais devem acompanhar a implantação para que a página de documentação possa oferecê-los.

## 3. Caminho do banco e separação de ambientes

A aplicação obtém o caminho do banco por meio da variável de ambiente **`PRESTSERV_DB_PATH`**, quando definida; caso contrário, utiliza o caminho padrão configurado em `conn/database.py`, normalmente `dados/PrestServ.db` na raiz do repositório.

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
python -m bd_schemes.inicializar_banco
python -m scripts.criar_admin
```

A criação inicial deve configurar a conta **superadmin** e disponibilizar as tabelas do esquema V2, inclusive cadastros, atendimentos, serviços, quantidades, entradas, voluntários, presenças de voluntários, fotos e logs.

**Não execute esses comandos em produção antes de confirmar como o diretório persistente está montado.** A aplicação também chama `inicializar_banco()` no fluxo de inicialização normal.

## 6. Versão do esquema e migração controlada

A V2 trabalha com `PRAGMA user_version = 2` no SQLite. Esse número é a versão **do esquema do banco**, não a versão do software. Bancos de versões anteriores exigem migração controlada.

O `bd_schemes/inicializar_banco.py` da V2 foi preparado para **recusar a inicialização de um banco existente que não esteja no esquema esperado**. Essa proteção evita alterações implícitas em um banco antigo e não deve ser contornada alterando manualmente `PRAGMA user_version`.

### 6.1. Verificar a situação da produção (somente leitura)

Identifique o caminho de dados real do contêiner e faça uma cópia de segurança. Em um ambiente de inspeção apropriado, verifique:

```sql
PRAGMA user_version;
PRAGMA integrity_check;
PRAGMA foreign_key_check;
```

Registre também as tabelas e colunas existentes. A produção pode estar na V1.0 ou em um estado intermediário da V1.1.0; **não presuma a origem sem inspecionar o arquivo efetivamente implantado**.

### 6.2. Migrar uma cópia isolada

O script `scripts/migrar_prestserv_v200.py` utiliza o mecanismo de cópia do SQLite para criar **outro arquivo de banco**, preservando o arquivo de origem. Ele não atualiza o banco original em seu lugar.

Exemplo, **somente se o banco de origem indicado for de fato o arquivo V1 que se deseja migrar**:

```bash
python -m scripts.migrar_prestserv_v200 \
  --origem dados/PrestServ.db \
  --saida dados/PrestServ_v2_homologacao.db
```

O arquivo de destino **não pode existir** antes da execução. O script solicita o login de um administrador ativo, que passa a `superadmin` somente na cópia produzida. Depois, verifique `PRAGMA user_version = 2`, `integrity_check = ok`, ausência de violações de chaves estrangeiras e preservação das contagens dos registros antigos.

Na preparação da V2.0.0, a migração V1 → V2 foi concluída com sucesso em uma cópia de homologação e o usuário confirmou sete testes funcionais na aplicação. **Esse resultado não substitui a migração final de uma cópia recém-obtida do banco efetivamente usado no servidor**, nem a verificação do código após a reorganização manual dos módulos.

Para a migração final, durante a janela de manutenção:

1. Impedir novas gravações na V1 e gerar um **backup consistente** da produção, de preferência preservando também a imagem/commit em uso.
2. Identificar o banco real por sua montagem Docker/Portainer; verificar sua versão do esquema e integridade.
3. Migrar o backup para um **novo arquivo**, no ambiente com o código da V2, sem substituir ainda o banco de origem.
4. Conferir contagens, vínculos, usuários, fotos, serviços e amostras de atendimentos; validar o login da conta promovida.
5. Somente depois das verificações, planejar a troca do arquivo persistente durante a parada do serviço, com possibilidade documentada de restauração do banco original.

**Não** use comandos de inicialização para forçar um banco antigo a parecer V2, nem altere `PRAGMA user_version` manualmente. Se o esquema original diferir do homologado, interrompa a publicação e analise a divergência antes de continuar.

### 6.3. Critérios de aprovação

- `PRAGMA user_version` igual a `2` no banco migrado.
- `PRAGMA integrity_check` retornando `ok`.
- `PRAGMA foreign_key_check` sem resultados.
- Contagens e amostras de pessoas, fotos, serviços, presenças, usuários e logs preservadas; conferência de campos novos e valores padrão.
- Pelo menos um superadministrador ativo e contas dos demais perfis configuradas conscientemente.
- Backup da V2 validado e restauração testada na cópia isolada, sem alteração do banco original.

## 7. Controle de acesso da V2

A aplicação possui cinco papéis: `superadmin`, `admin`, `secretaria`, `porteiro`, `consulta`. O superadmin administra usuários, logs e backup; o admin opera cadastros, correções e relatórios; secretaria opera cadastros e entradas; porteiro registra presenças somente do dia; consulta acessa apenas dados agregados.

As permissões precisam ser verificadas na camada que fornece acesso aos dados, não apenas pela visibilidade do menu. A tela de documentação também revalida a conta ativa antes de ler ou disponibilizar cada PDF.

## 8. Backup e restauração

### 8.1. Backup

O módulo `services/backup.py` prepara uma cópia consistente do SQLite e a inclui em um arquivo ZIP, com arquivo interno `prestserv.db`. Na V2, o backup contém as tabelas operacionais e também os dados de **voluntários, fotografias de voluntários e presenças de voluntários**.

A geração de backup completo pela interface é restrita ao **superadministrador**. Os ZIPs contêm dados pessoais, informações cadastrais e hashes de senha; devem ser guardados de maneira protegida, preferencialmente fora do servidor principal. Não os envie ao Git.

### 8.2. Validação e restauração

Antes de restaurar, a aplicação valida a estrutura esperada do banco V2, sua integridade e a autorização do operador. A falta de tabelas essenciais do voluntariado impede a restauração.

A restauração **substitui o conteúdo atual**: operações realizadas após o backup restaurado podem se perder. Não execute a restauração enquanto outros usuários estiverem atendendo. Reautentique e confira dados e logs após a operação.

Nos testes isolados da V2, foram validadas preservação de cadastros, fotos e presenças de voluntários, bloqueio para o perfil Consulta, auditoria de restauração e rejeição de backups incompletos. **Esses testes não substituem a homologação do banco real migrado.**

## 9. Implantação com Git, Portainer e Nginx

A instalação de produção existente utiliza um repositório Git no servidor e é gerenciada pelo **Portainer**, com aplicação em Docker e acesso via Nginx. **Não é necessário criar uma implantação paralela ou substituir a organização atual por um Compose novo**. Os detalhes do stack/contêiner ainda precisam ser confirmados no Portainer.

A publicação deverá partir de um commit aprovado, preferencialmente em um branch de release específico, por exemplo `release/v2.0.0`. No servidor, a troca do branch via Git atualiza os arquivos do repositório, mas **não atualiza por si só uma imagem Docker existente**; o mecanismo de build/redeploy depende de como a instalação atual monta ou constrói o código. A versão V1 deve permanecer recuperável.

Antes de executar comandos de implantação, confira no Portainer: imagem ou build, volumes/bind mounts (principalmente o SQLite), variáveis de ambiente, rede, portas, política de reinício e relação com o Nginx. Nunca migre ou sobrescreva o banco enquanto houver escrita concorrente.

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

## 10. Documentação na aplicação e temas

A tela `telas/tela_documentacao.py` foi acrescentada durante a preparação da versão para disponibilizar os PDFs da pasta `docs/` conforme as permissões de cada perfil. O `app.py` integra essa tela à navegação; a leitura e o download precisam respeitar o perfil ativo e a revalidação da conta no SQLite. O componente `st.pdf` exige a dependência opcional de PDF do Streamlit, registrada no `requirements.txt` como `streamlit[pdf]`.

Confirme que os arquivos PDF estão presentes na imagem ou no diretório disponibilizado ao contêiner. Regenerar os arquivos Markdown não atualiza automaticamente os PDFs sem executar `bash docs/gerar_manuais.sh`.

### Temas e identidade visual

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

**Banco não encontrado:** confira `PRESTSERV_DB_PATH` e `conn/database.py`, o nome do arquivo (inclusive maiúsculas/minúsculas) e a montagem do volume.

**`database is locked`:** verifique acessos concorrentes, transações longas e operações de backup/restauração. Não sobrescreva o SQLite enquanto está em uso.

**Falha no Nginx/WebSocket:** confira proxy reverso, cabeçalhos de upgrade, origem da rota e portas internas da aplicação.

**PDF com fonte ou acentos incorretos:** confira fontes do ReportLab para os relatórios da aplicação, e Pandoc/XeLaTeX, `estilo_pdf.tex` e pacotes de idioma para os manuais.

**Tema não alterna:** confirme o `.streamlit/config.toml` da imagem executada e reinicie o serviço após editar a configuração.

## 14. Autoria e responsabilidade

**Desenvolvido por Jeronimo Costa Penha.** A instituição é responsável pelas políticas locais de acesso, guarda de backups, privacidade, manutenção e continuidade operacional.

