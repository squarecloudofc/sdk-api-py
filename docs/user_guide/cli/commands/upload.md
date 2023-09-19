# :material-upload: Fazendo upload de uma aplicação

Para realizar o upload de uma aplicação é bem simples, basta fornecer um zip
com os arquivos necessários, consulte
este [guia](https://docs.squarecloud.app/introduction)

# Uso

````title=""
--8<-- "examples/upload_app/with_cli.sh"
````

## Arguments:

{{ read_csv('./docs/commands_csv/upload/arguments.csv') }}

## Options:

{{ read_csv('./docs/commands_csv/upload/options.csv') }}

??? nota nota

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
