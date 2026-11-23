# Imagens Docker do PrestServ

## Arquivos por versão

- `v1.0/Dockerfile`: deve conter a cópia fiel do Dockerfile usado na V1 em produção; **ainda precisa ser incorporado**.
- `v2.0.0/Dockerfile`: proposta inicial da imagem V2, com Python 3.14 e bibliotecas do `requirements.txt`.
- `/.dockerignore`: fica na raiz do repositório porque o contexto de build é a raiz (`.`).

## Construir a V2 (somente após validar o Dockerfile atual da V1)

A partir da raiz do projeto, com o código no commit da versão desejada:

```bash
docker build -f docker/v2.0.0/Dockerfile -t prestserv:2.0.0 .
```

A tag Git `V2.0.0` identifica um commit; a imagem Docker `prestserv:2.0.0` é um artefato construído a partir do código desse commit. A existência de uma tag Git não cria automaticamente a imagem.

## Implantação existente

A stack atual usa `image: prestserv:1.0` e monta **todo o projeto** em `/app`:

```yaml
volumes:
  - /server/containers/PrestServ/PrestServ:/app
```

Essa montagem tem prioridade sobre os arquivos copiados para `/app` durante o build. Por isso, **uma simples troca de imagem não congela a versão do código**: o Git no host precisa permanecer no commit correto enquanto o contêiner estiver ativo.

Não execute `git checkout` ou `git pull` na pasta montada enquanto houver atendimentos. Preserve a estrutura do Nginx e a rede `homelab_proxy`.

Antes da implantação V2: obter backup recuperável, migrar **cópia atualizada** do SQLite, testar, parar as operações, trocar o arquivo do banco durante janela de manutenção, conferir permissões de escrita e atualizar/recriar o contêiner. Mantenha o banco original para rollback.

## Atenções

- O Dockerfile V2 é **proposto, ainda não testado por build real** nem comparado ao Dockerfile de produção da V1.
- O Dockerfile V2 usa o usuário padrão da imagem até conhecermos as permissões da montagem atual. Depois da publicação, podemos endurecer a execução com usuário não privilegiado e montagem exclusiva dos dados.
- `dados/`, backups e segredos nunca devem entrar na imagem ou no Git.
- Para voltar à V1 é necessário recuperar **código, imagem e banco V1 compatível**.
