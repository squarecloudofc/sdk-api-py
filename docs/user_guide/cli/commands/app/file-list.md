# :material-view-list: Obtendo uma lista de arquivos

Com o sub-comando `file-list` você pode obter uma lista com informações dos
arquivos da sua aplicação, tais como:

- `Last Modified`: O timestamp da última modificação do arquivo ou diretório em
  milissegundos.
- `Name`: O nome do arquivo/diretório.
- `Path`: O caminho do arquivo/diretório.
- `Type`: Informa se é um arquivo ou um diretório.

## Uso

````title=""
--8<-- "examples/file_list/with_cli.sh"
````

## Arguments

{{ read_csv('./docs/commands_csv/app/file-list/arguments.csv') }}