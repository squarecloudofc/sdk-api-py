[CLI]: cli/introduction.md

# :material-folder-key: Guardando sua API key

Na maioria dos comandos da [CLI], é necessário providenciar sua API key, isto pode ser
feito passando a opção `--token`, como pode observar no exemplo abaixo:

!!! example

    ```bash
    squarecloud app-list --token <YOUR_API_TOKEN>
    ```

Porém, eu não considero esta uma boa forma de informar a key, para isso há uma
alternativa bem melhor.

## Variáveis de ambiente:

Alternativamente, você pode definir sua API key como uma variável de ambiente
chamada `SQUARECLOUD-TOKEN`. O comando irá automaticamente ler esta variável de
ambiente se a opção `--token` não for usada.

### Definindo sua variável de ambiente:

Para definir uma variável de ambiente chamada SQUARECLOUD-TOKEN basta usar o
comando abaixo conforme o seu sistema operacional

=== "Windows"

    ```cmd
    setx SQUARECLOUD-TOKEN "<YOUR_API_TOKEN>"
    ```

=== "Linux"

    ```bash
    export SQUARECLOUD-TOKEN=<YOUR_API_TOKEN>
    ```
