import os

from dotenv import load_dotenv

import squarecloud

load_dotenv()
client = squarecloud.Client(os.getenv('KEY'))
