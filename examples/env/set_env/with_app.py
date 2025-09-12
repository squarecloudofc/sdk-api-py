import asyncio

from squarecloud import Client

client = Client(api_key="your_api_key")


async def main():
    envs = {"KEY": "VALUE"} # The environment variables you want to set
    app = await client.app("your_app_id")
    result = await app.set_envs(envs) # Sets or updates the specified environment variables
    print("Set envs result:", result)

asyncio.run(main())