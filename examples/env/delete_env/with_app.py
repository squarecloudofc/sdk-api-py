import asyncio

from squarecloud import Client

client = Client(api_key="your_api_key")

async def main():
    app = await client.app("your_app_id")
    keys = [] # The keys you want to delete
    result = await app.delete_envs(keys) # Deletes the specified environment variables
    print("Remaining env variables: ", result) 

asyncio.run(main())