# :material-file-cog: Criando arquivo de configuração

O comando `create-config-file` permite criar um arquivo de configuração que é
usado para realizar um upload da sua aplicação.

Este arquivo de configuração contém detalhes sobre a sua aplicação, 
como nome de exibição,
memória, versão, avatar, descrição, domínio, comando de inicialização e opções
de reinício automático. Este guia explica como usar o comando e todos os
parâmetros associados a ele.

## Uso

Para usar o comando `create-config-file`, execute o seguinte no seu terminal:

````title=""
--8<-- "examples/creating_config_file/with_cli.sh"
````

O comando solicitará várias informações para preencher o arquivo de
configuração. Você será guiado pelas opções interativas para inserir os
detalhes necessários. Aqui estão as opções disponíveis:

## Arguments

{{ read_csv('./docs/commands_csv/create-config-file/arguments.csv') }}

## Options:

{{ read_csv('./docs/commands_csv/create-config-file/options.csv') }}
