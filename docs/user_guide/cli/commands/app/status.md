# :simple-statuspal: Obtendo status de uma aplicação

O sub-comando `status` exibe alguns status da sua
aplicação, sendo eles:

- `Cpu`: O uso de CPU da sua aplicação.
- `Ram`: O uso de RAM da sua aplicação.
- `Network`: Informações de tráfego da sua aplicação.
- `Requests`: Contagem de requests da sua aplicação.
- `Running`: Indica se a sua aplicação está em execução.
- `Status`: Status atual da sua aplicação (pode ser 'created', 'starting', '
  restarting', 'running' ou 'deleting').
- `Storage`: Armazenamento usado pela sua aplicação.
- `Uptime`: Uptime da sua aplicação em milisegundos.

## Uso:

````title=""
--8<-- "examples/getting_application_status/with_cli.sh"
````
