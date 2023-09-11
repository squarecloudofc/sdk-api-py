import squarecloud as square

client = square.Client(api_key='API KEY')


async def example():
    data = await client.app_data('application_id')
    print(data)  # AppData(...)
