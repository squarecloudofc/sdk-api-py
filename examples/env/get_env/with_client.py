import asyncio

from squarecloud import Client

client = Client(api_key="your_api_key")


async def main():
    envs = await client.get_app_envs("app_id")
    print("App envs: ", envs)

asyncio.run(main())