import squarecloud as square

client = square.Client(api_key='API KEY')


async def example():
    app = await client.app('application_id')
    files_list = await app.files_list(path='/')  # list[FileInfo(...)]

    for file in files_list:
        print(file.name)  # 'main.py'

        print(file.type)  # 'directory' or 'file'

        print(file.size)  # 2140

        print(file.lastModified)  # 1677112835000
