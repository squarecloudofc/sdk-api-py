import squarecloud as square

client = square.Client(api_key='API KEY')


async def example():
    statistics = await client.statistics()
    print(statistics)  # StatisticsData(...)
