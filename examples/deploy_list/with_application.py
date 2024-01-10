import squarecloud as square

client = square.Client(api_key='API KEY')


async def example():
    app = await client.app('application_id')
    deploys = await app.last_deploys()
    print(deploys)  # [[DeployData(...), DeployData(...), DeployData(...)]]
