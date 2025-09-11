import asyncio

from squarecloud import Client

client = Client(api_key="your_api_key")


async def main():
    keys = []  # The keys you want to delete
    result = await client.delete_app_envs("app_id", keys) # Deletes the specified environment variables
    print("Remaining env variables: ", result)

asyncio.run(main())