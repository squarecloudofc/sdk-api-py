import asyncio

from squarecloud import Client

client = Client(api_key="your_api_key")


async def main():
    app = await client.app("your_app_id")
    envs = await app.get_envs()
    print("App envs: ", envs)

asyncio.run(main())