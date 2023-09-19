[Client]: client.md

[Application]: ../../api_reference/Application.md

# :material-robot: Application

Usando o [Client] você pode obter um objeto (ou uma lista de
objetos) que representa sua aplicação, esse objeto seria uma instância da
classe [Application] que você pode usar
para gerenciar sua aplicação de forma mais prática, sem precisar sempre passar
o ‘id’ da sua aplicação.

???+ exemplo example

    ````{.py3 hl_lines="10 20 23 26 29 32 36 39" linenums="1"}
    --8<-- "examples/obtaining_app/with_client.py"
    ````

Você também pode obter uma lista de todas as suas aplicações

???+ exemplo example

    ````{.py3 hl_lines="10 20 23 26 29 32 36 39" linenums="1"}
    --8<-- "examples/app_list/with_client.py"
    ````
