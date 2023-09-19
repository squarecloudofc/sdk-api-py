[Client]: client.md

[Application]: application.md

[StatisticsData]: ../../../api_reference/data_classes/StatisticsData/

[StatusData]: ../../../api_reference/data_classes/StatusData/

[LogsData]: ../../../api_reference/data_classes/LogsData/

[Response]: ../../../api_reference/Response/

[client.app_status]: ../../../api_reference/Client/#client.Client.app_status

[app.status]: ../../../api_reference/Application/#app.Application.status

[client.get_logs]: ../../../api_reference/Client/#client.Client.get_logs

[app.logs]: ../../../api_reference/Application/#app.Application.logs

[app.status]: ../../../api_reference/Application/#app.Application.status

[app.start]: ../../../api_reference/Application/#app.Application.start

[app.delete]: ../../../api_reference/Application/#app.Application.delete

[client.start_app]: ../../../api_reference/Client/#client.Client.start_app

[app.stop]: ../../../api_reference/Application/#app.Application.stop

[client.stop_app]: ../../../api_reference/Client/#client.Client.stop_app

[app.restart]: ../../../api_reference/Application/#app.Application.restart

[client.restart_app]: ../../../api_reference/Client/#client.Client.restart_app

[client.delete_app]: ../../../api_reference/Client/#client.Client.delete_app

# :material-cog: Gerenciando sua aplicação

Nesta seção, você aprenderá a gerenciar sua aplicação usando a biblioteca
disponível. Você pode interagir com sua aplicação de diversas maneiras, como
obtendo informações sobre o status da aplicação, acessando logs, iniciando,
parando e reiniciando a aplicação, bem como gerenciando arquivos associados a
ela.

Todas as operações abaixo podem ser feitas pela classe [Client] ou a
classe [Application]. A seguir, estão exemplos de como realizar cada uma das
tarefas
usando ambas as classes:

## :simple-statuspal: Obtendo o status da sua aplicação:

[client.app_status] e [app.status] retornam um objeto [StatusData].

=== "Usando Client"

    ```.py3 hl_lines="3 9"

    --8<-- "examples/getting_application_status/with_client.py"
    ```

=== "Usando Application"

    ```.py3 hl_lines="3 9"

    --8<-- "examples/getting_application_status/with_application.py"
    ```

## :material-file-document: Obtendo logs:

[client.get_logs] e [app.logs] retornam um objeto [LogsData].

=== "Usando Client"

    ```.py3 hl_lines="7"

    --8<-- "examples/getting_logs/with_client.py"
    ```

=== "Usando Application"

    ```.py3 hl_lines="8"

    --8<-- "examples/getting_logs/with_application.py"
    ```

## :material-cog-play: Ligando aplicação

[client.start_app] e [app.start] retornam um objeto [Response].

=== "Usando Client"

    ```.py3 hl_lines="7"

    --8<-- "examples/starting_app/with_client.py"
    ```

=== "Usando Application"

    ```.py3 hl_lines="8"

    --8<-- "examples/starting_app/with_application.py"
    ```

## :material-cog-stop: Desligando aplicação

[client.stop_app] e [app.stop] retornam um objeto [Response].

=== "Usando Client"

    ```.py3 hl_lines="7"

    --8<-- "examples/stopping_app/with_client.py"
    ```

=== "Usando Application"

    ```.py3 hl_lines="8"

    --8<-- "examples/stopping_app/with_application.py"
    ```

## :material-cog-refresh: Reiniciando aplicação

[client.restart_app] e [app.restart] retornam um objeto [Response].

=== "Usando Client"

    ```.py3 hl_lines="7"

    --8<-- "examples/restarting_app/with_client.py"
    ```

=== "Usando Application"

    ```.py3 hl_lines="8"

    --8<-- "examples/restarting_app/with_application.py"
    ```

## :material-delete: Deletando uma aplicação

[client.delete_app] e [app.delete] retornam um objeto [Response]

=== "Usando Client"

    ```.py3 hl_lines="7"

    --8<-- "examples/deleting_application/with_client.py"
    ```

=== "Usando Application"

    ```.py3 hl_lines="8"

    --8<-- "examples/deleting_application/with_application.py"
    ```

!!! Aviso warning

    Isso irá deletar a sua aplicação **PERMANENTEMENTE**, isso significa que,
    a menos que você possua um backup de sua aplicação, ela não poderá ser
    recuperada.
