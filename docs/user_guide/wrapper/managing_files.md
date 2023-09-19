[Client]: client.md

[Application]: application.md

[Response]: ../../../api_reference/Response/

[client.app_files_list]: ../../../api_reference/Client/#client.Client.app_files_list

[app.files_list]: ../../../api_reference/Application/#app.Application.files_list

[client.read_app_file]: ../../../api_reference/Client/#client.Client.read_app_file

[app.read_file]: ../../../api_reference/Application/#app.Application.read_file

[client.create_app_file]: ../../../api_reference/Client/#client.Client.create_app_file

[app.create_file]: ../../../api_reference/Application/#app.Application.create_file

[client.delete_app_file]: ../../../api_reference/Client/#client.Client.delete_app_file

[app.delete_file]: ../../../api_reference/Application/#app.Application.delete_file

[FileInfo]: ../../../api_reference/data_classes/FileInfo/

# :material-folder: Manipulação de Arquivos da Aplicação

Nesta seção, você encontrará informações e exemplos sobre como manipular os
arquivos associados à sua aplicação. Aprenda a listar, ler, criar e excluir
arquivos usando o Cliente ou a classe Application para uma administração
eficiente dos recursos da sua aplicação.

Todas as operações abaixo podem ser feitas pela classe [Client] ou a
classe [Application]. A seguir, estão exemplos de como realizar cada uma das
tarefas
usando ambas as classes:

## :material-file-find: Obtendo uma lista de arquivos:

[client.app_files_list] e [app.files_list] retornam uma lista de [FileInfo].

=== "Usando Client"

    ```.py3 hl_lines="7"

    --8<-- "examples/file_list/with_client.py"
    ```

=== "Usando Application"

    ```.py3 hl_lines="8"

    --8<-- "examples/file_list/with_application.py"
    ```

## :material-file-eye: Lendo um arquivo:

[client.read_app_file] e [app.read_file] retornam um objeto `BytesIO`.

=== "Usando Client"

    ```.py3 hl_lines="7-9"

    --8<-- "examples/read_file/with_client.py"
    ```

=== "Usando Application"

    ```.py3 hl_lines="8"

    --8<-- "examples/read_file/with_application.py"
    ```

## :material-file-plus: Criando um arquivo:

[client.create_app_file] e [app.create_file] retornam um objeto [Response].

=== "Usando Client"

    ```.py3 hl_lines="7-11"

    --8<-- "examples/create_file/with_client.py"
    ```

=== "Usando Application"

    ```.py3 hl_lines="9-12"

    --8<-- "examples/create_file/with_application.py"
    ```

## :material-file-minus: Deletando um arquivo:

[client.delete_app_file] e [app.delete_file] retornam um objeto [Response].

=== "Usando Client"

    ```.py3 hl_lines="7"

    --8<-- "examples/delete_file/with_client.py"
    ```

=== "Usando Application"

    ```.py3 hl_lines="9"

    --8<-- "examples/delete_file/with_application.py"
    ```

---

[//]: # (## :simple-alwaysdata: Squarecloud Statistics)

[//]: # ()

[//]: # (Você pode obter estatísticas sobre a hospedagem)

[//]: # (usando [Client.statistics&#40;&#41;]&#40;../../../api_reference/Client/#client.Client.statistics&#41;)

[//]: # (.)

[//]: # ()

[//]: # (Esta função retorna um objeto [StatisticsData].)

[//]: # ()

[//]: # (``` .py3 title="" hl_lines="7")

[//]: # (--8<-- "examples/squarecloud_statistics.py")

[//]: # (```)
