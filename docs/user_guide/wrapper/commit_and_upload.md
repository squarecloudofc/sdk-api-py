[Client]: client.md

[Application]: application.md

[squarecloud.File]: ../../../api_reference/File/

# :material-upload: Commit e Upload

Você pode fazer commits e uploads usando [Client] ou [Application], você
precisa apenas de um objeto [squarecloud.File] e passar o caminho onde seu
arquivo zip está.

## :octicons-git-commit-16: Fazendo um Commit:

=== "Usando Client"

    ``` python
    --8<-- "examples/commit/with_client.py"
    ```

=== "Usando Application"

    ``` python
    --8<-- "examples/commit/with_application.py"
    ```

___

## :material-cloud-upload: Fazendo um upload:

Para fazer upload de uma aplicação você usa apenas o [Client].

!!! exemplo example

    ```{.py3 hl_lines="8"}
    --8<-- "examples/upload_app/with_client.py"
    ```

**lembrando que para fazer upload de uma aplicação é necessário um zip que
contenha (pelo menos) os seguintes arquivos**:

- arquivo principal: aquele responsável por iniciar sua aplicação
- arquivo de dependências: contém informações sobre quais dependências são
  necessárias
- arquivo de configuração (squarecloud.app): um arquivo de configuração
  especificando o nome,
  descrição, nome do arquivo principal, versão, etc. Para saber mais sobre o
  arquivo de configuração dê uma olhada neste
  [guia](https://docs.squarecloud.app/articles/how-to-create-your-squarecloud-configuration-file)

??? dica tip

    Para sua conveniência, foi adicionada uma função para criar esse arquivo de 
    configuração:
    [create_config_file](../../../api_reference/create_config_file/)

    Confira também como criar o arquivo de configuração usando a linha de 
    comando
    [create_config_file](../../../user_guide/cli/commands/create_config_file/)
