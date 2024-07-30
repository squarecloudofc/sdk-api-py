import squarecloud as square

client = square.Client(api_key='API KEY')


async def example():
    webhook_url = await client.github_integration(
        'application_id', access_token='access_token'
    )
    print(webhook_url)
