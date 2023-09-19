[capture_listeners]: capture_listeners.md

[Client]: client.md

# :material-ear-hearing: Request Listeners

Os "request listeners" fazem praticamente a mesma coisa
que [capture_listeners]. Mas aqui você
usa o [Client] e os retornos de todos os endpoints
são objetos `squarecloud.http.Response`.

??? Nota note

    Para melhor entendimento leia primeiro [capture_listeners]

!!! exemplo example

    ```{.py3 hl_lines="7-9 12-14" title="example.py"}
    --8<-- "examples/request_listener.py"
    ```

???+ Dica tip

    Você pode usar o parâmetro `avoid_listener=True` para que o listener 
    não seja chamado