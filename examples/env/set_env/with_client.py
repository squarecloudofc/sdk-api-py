import asyncio

from squarecloud import Client

client = Client(api_key="your_api_key")


async def main():
    envs = {"KEY": "VALUE"} # The environment variables you want to set
    result = await client.set_app_envs("app_id", envs) # Sets or updates the specified environment variables
    print("Set envs result:", result)

asyncio.run(main())