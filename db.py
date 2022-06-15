import pymongo
import os
from dotenv import load_dotenv
load_dotenv('./.env')


MONGDB_URI = os.getenv('MONGDB_URI')
client = pymongo.MongoClient(MONGDB_URI)


def get_collection(database, collection):
    db = client[database]
    return db[collection]
