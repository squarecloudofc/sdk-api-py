import squarecloud as square

client = square.Client(api_key='API KEY')


async def example():
    webhook_url = await client.github_integration(
        'application_id', access_token='access_token'
    )
    print(
        webhook_url
    )  # https://api.squarecloud.app/v2/git/webhook/<webhook-code>
