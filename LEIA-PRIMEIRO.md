# Pacote de organização Docker — PrestServ

Copie `docker/` para a raiz do repositório. Confira/mescle `/.dockerignore` antes de substituir uma versão existente.

**Não há Dockerfile V1 no pacote**, pois ele deve ser copiado exatamente do servidor; preservamos um README em `docker/v1.0/` como lembrete.

Este pacote não altera o Portainer, não cria imagens, não migra banco e não faz checkout de Git.

Primeiro, envie/compare o Dockerfile V1 real e teste um build da V2. Somente depois prepare a publicação e a tag Git `V2.0.0`.
