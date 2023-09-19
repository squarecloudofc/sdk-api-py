# :fontawesome-solid-user: Client

O objeto central é o objeto Client, instanciado com uma [chave de API](../getting_api_key.md). Esse
objeto representa uma conexão com o serviço SquareCloud e atua como uma
‘interface’ para interagir com vários aspectos do serviço.

!!! exemplo example

    ```{.py hl_lines="4"}
    --8<-- "examples/client_example.py"
    ```

## Parâmetros:

### api_key

`api_key: str`: Este é o parâmetro necessário ao instanciar o objeto Client.
Deve ser fornecida a chave de API válida como uma string para que a
autenticação possa ser realizada corretamente.

### debug

`debug: bool = True`: Este é um parâmetro opcional que controla o modo de
depuração do objeto Client. Quando definido como True, toda vez que uma request
é feita, o objeto Client imprime informações de depuração para facilitar a
detecção e resolução de
problemas. No entanto, em ambientes de produção, é comum definir esse parâmetro
como False para evitar a exibição de informações desnecessárias.
Este valor por padrão é True.

```{.py3 hl_lines="3" linenums="1" title="example.py"}
import squarecloud as square

client = square.Client(api_key='API KEY', debug=False)  # no logs
```