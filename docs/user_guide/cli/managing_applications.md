# app

Este comando agrupa várias operações relacionadas a aplicativos.

Usage: squarecloud app [OPTIONS] [APP_ID] COMMAND [ARGS]...

Options:
  -t, --token TEXT  your api token  [required]
  --help            Show this message and exit.

Commands:

- backup
- commit
- data
- delete
- file-create
- file-delete
- file-list
- file-read
- logs
- restart
- start
- status
- stop

- ## :simple-statuspal: app status

Obtém o status de um aplicativo específico.

````bash
$ squarecloud app app_id status
````

Opções:

- --token ou -t: sua chave de API para autenticação na plataforma. Esta opção é
  obrigatória.
- app_id: O ID do aplicativo para o qual você deseja obter o status.

## :material-view-list: app-list

Lista todos os seus aplicativos na plataforma SquareCloud.

````bash
$ squarecloud app-list
````

Opções:

- --token ou -t: Sua chave de API para autenticação na plataforma. Esta opção é 
  obrigatória.

## app data

Obtém informações detalhadas sobre um aplicativo específico.

````bash
$ squarecloud app app_id data
````

Opções:

--token ou -t: Sua chave de API para autenticação na plataforma. Esta opção é
obrigatória.
app_id: O ID do aplicativo para o qual você deseja obter informações
detalhadas.
app logs
Obtém os logs de um aplicativo específico.

````bash
$ squarecloud app app_id logs
````

Opções:

--token ou -t: Sua chave de API para autenticação na plataforma. Esta opção é
obrigatória.
app_id: O ID do aplicativo para o qual você deseja obter os logs.
app backup
Realiza um backup de um aplicativo específico.

````bash
$ squarecloud app app_id backup
````

Opções:

--token ou -t: Sua chave de API para autenticação na plataforma. Esta opção é
obrigatória.
app_id: O ID do aplicativo para o qual você deseja realizar o backup.
app start
Inicia um aplicativo específico.

````bash
$ squarecloud app app_id start
````

Opções:

--token ou -t: Sua chave de API para autenticação na plataforma. Esta opção é
obrigatória.
app_id: O ID do aplicativo que você deseja iniciar.
app stop
Para a execução de um aplicativo específico.

````bash
$ squarecloud app app_id stop
````

Opções:

--token ou -t: Sua chave de API para autenticação na plataforma. Esta opção é
obrigatória.
app_id: O ID do aplicativo que você deseja parar.
app restart
Reinicia um aplicativo específico.

````bash
$ squarecloud app app_id restart
````

Opções:

--token ou -t: Sua chave de API para autenticação na plataforma. Esta opção é
obrigatória.
app_id: O ID do aplicativo que você deseja reiniciar.
app delete
Exclui um aplicativo específico.

````bash
$ squarecloud app app_id delete
````
