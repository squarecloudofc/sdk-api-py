import squarecloud as square
from squarecloud.data import StatusData

client = square.Client(api_key='API_KEY')


async def example():
    app_status: StatusData = await client.app_status('application_id')
    print(app_status)
