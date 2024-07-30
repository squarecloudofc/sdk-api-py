import squarecloud as square

client = square.Client(api_key='API KEY')


async def example():
    webhook_url = await client.current_app_integration(
        'application_id',
    )
    print(webhook_url)
