from asyncio.log import logger
import pymongo
import os
from dotenv import load_dotenv
load_dotenv('./.env')


MONGODB_URI = os.getenv('MONGODB_URI')
client = pymongo.MongoClient(MONGODB_URI)


def get_collection(database, collection):
    db = client[database]
    return db[collection]
