import os
from django.conf import settings
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()


class MongoConnection:
    def __init__(self):
        self.client = MongoClient(settings.MONGODB_URI)
        self.db = self.client[settings.DATACUBE_V2_AUTH_DB]

    def get_collection(self, collection_name):
        return self.db[collection_name]

# Instantiate the connection
mongo_conn = MongoConnection()