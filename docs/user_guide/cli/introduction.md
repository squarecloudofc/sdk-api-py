# :material-console: Introdução

A CLI (Interface de Linha de Comando) oferece uma forma conveniente
de interagir com a plataforma SquareCloud e gerenciar vários aspectos das suas
aplicações. Ela disponibiliza um conjunto de
comandos que permitem a execução de ações como recuperar informações de
aplicações, verificar o status, acessar logs, realizar backups e mais.
Esta documentação o guiará através dos comandos disponíveis e seu
uso.

## Uso Básico

Após a instalação, você pode usar a CLI executando os comandos
relevantes. Aqui estão alguns exemplos básicos:

??? dica tip

    Nos exemplos abaixo, estamos informando a chave da API por meio da opção
    --token. No entanto, existe uma forma mais prática de configurar a autenticação
    da CLI, permitindo que você evite a repetição constante da chave em cada
    comando, você verá isso na próxima
    seção [Guardando sua API key](storing_your_token.md).

Para obter informações sobre uma aplicação:

````bash
$ squarecloud app <app_id> --token <seu_token>
````

Para listar todas as aplicações:

````bash
$ squarecloud app-list --token <seu_token>
````

Para fazer upload de uma aplicação:

````bash
$ squarecloud upload <caminho_do_arquivo> --token <seu_token>
````

Certifique-se de substituir `<app_id>`, `<caminho_do_arquivo>` e `<seu_token>`
pelos
valores corretos.

