import asyncio

from squarecloud import Client

client = Client(api_key="your_api_key")


async def main():
    envs = {"ONLY_THIS": "present"} # The new environment variables
    result = await client.overwrite_app_envs("app_id", envs) # Overwrites all environment variables and sets only the new ones
    print("Overwrite envs result:", result)

asyncio.run(main())