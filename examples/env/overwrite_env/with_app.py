import asyncio

from squarecloud import Client

client = Client(api_key="your_api_key")


async def main():
    app = await client.app("your_app_id")
    envs = {"KEY": "VALUE"} # The new environment variables
    result = await app.overwrite_env(envs) # Overwrites all environment variables and sets only the new ones
    print("Overwrite envs result: ", result)

asyncio.run(main())