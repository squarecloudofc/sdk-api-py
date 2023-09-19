[Endpoint.app_status()]: ../../../api_reference/Endpoint/#http.endpoints.Endpoint.app_status

[Endpoint.logs()]: ../../../api_reference/Endpoint/#http.endpoints.Endpoint.logs

[Endpoint.backup()]: ../../../api_reference/Endpoint/#http.endpoints.Endpoint.backup

[cache]: ../application_cache/

# :material-ear-hearing: Capture Listeners

_esta implementação é baseada em
uma [sugestão](https://github.com/squarecloudofc/wrapper-api-py/pull/1) feita
por [@Mudinho](https://github.com/zRickz), obrigado por contribuir_

Às vezes é muito útil ter listeners para requests, com eles você pode
implementar
recursos que precisam ser chamados sempre que "algo" é feito em sua aplicação.

Por exemplo, imagine que toda vez que uma requisição para a rota '/logs' é
feita,
meu código executa alguma tarefa que verifica se as novas logs diferem
das antigas. Bem, vamos ver como isso pode ser feito:

!!! exemplo example

    ```{.py3 hl_lines="9-12"}
    --8<-- "examples/capture_listener.py"
    ```

??? Dica tip

    Você pode usar o parâmetro `avoid_listener=True` para que o listener da 
    aplicação não seja chamado

Como você deve ter notado, na primeira vez que a comparação entre os logs
acontece `after != before` retorna `True`, isso acontece precisamente
porque `after` é igual a `LogsData(logs=None)`, pois ainda não há nada
armazenados no [cache] interno.

???+ info "Outras informações sobre este decorador"

    - se você usa discord.py ou algum fork (provavelmente você usa), você deve
    saber que o que diferencia os eventos é o nome
    das funções que o decorador envolve, mas aqui difere, para saber
    qual
    rota da API o decorador precisa "ouvir", usamos o parâmetro `endpopint`, ele
    recebe uma classe `Endpoint`, então o nome da função que o decorador
    envolve fica a seu gosto.

    - a função que o decorador envolve pode ser na verdade, qualquer coisa que seja
    um callable. Isso inclui funções normais, corrotinas e até
    classes (`__init__` será chamado)

    - se o endpoint não for um [Endpoint.app_status()], [Endpoint.logs()] ou [Endpoint.backup()],
    apenas um parâmetro `response` (do tipo `squarecloud.http.Response`) será
    devolvida
