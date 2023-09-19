[cache.clear]: ../../../api_reference/AppCache/#app.AppCache.clear

[cache.update]: ../../../api_reference/AppCache/#app.AppCache.update

[StatusData]: ../../../api_reference/data_classes/StatusData/

[LogsData]: ../../../api_reference/data_classes/LogsData/

[BackupData]: ../../../api_reference/data_classes/BackupData/

[SquareException]: ../../../api_reference/Errors/#errors.SquareException

[Application.cache]: ../../../api_reference/AppCache/

# :material-content-save-check: Caching

Quando uma solicitação é feita, ela retorna informações do aplicativo e os
armazena em cache
no próprio objeto Application. Isso é útil caso você precise acessar essas
informações novamente
em um tempo considerável curto, ou seja, caso não valha a pena fazer uma nova
requisição à API para ter dados atualizados. Em casos como este você pode
acessar [Application.cache]

!!! exemplo example

    ```{.py3 hl_lines="11-13 21-23"}
    --8<-- "examples/app_cache/accessing_application_cache.py"
    ```

## :material-run-fast: Fazendo requests sem atualizar o cache

Se por algum motivo você não quiser atualizar o cache ao fazer uma request,
você pode passar o
argumento `update_cache=False`

!!! exemplo example

    ```{.py3 hl_lines="12-14"}
    --8<-- "examples/app_cache/avoid_update_cache.py"
    ```

Se os argumentos que você passa para [cache.update] não são uma instância
de [StatusData], [LogsData], ou [BackupData] um erro [SquareException] será
levantado

## :material-broom: Limpando o cache manualmente

Você pode limpar o cache manualmente
usando [cache.clear]

!!! exemplo example

    ```{.py3 hl_lines="17"}
    --8<-- "examples/app_cache/clear_cache.py"
    ```

## :material-update: Atualizando o cache manualmente

Você também pode atualizar manualmente usando [cache.update]

!!! exemplo example

    ```{.py3 hl_lines="17"}
    --8<-- "examples/app_cache/update_cache.py"
    ```
