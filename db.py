from asyncio.log import logger
import pymongo
import os
from dotenv import load_dotenv
load_dotenv('./.env')


MONGODB_URI = os.getenv('MONGODB_URI')
client = pymongo.MongoClient(
    "mongodb+srv://shubhjani:shubhjani@cluster0.xwfjb.mongodb.net/ifp-b2c-prod?authSource=admin&replicaSet=atlas-jq3j71-shard-0&w=majority&readPreference=primary&appname=MongoDB%20Compass&retryWrites=true&ssl=true")


def get_collection(database, collection):
    db = client[database]
    return db[collection]
