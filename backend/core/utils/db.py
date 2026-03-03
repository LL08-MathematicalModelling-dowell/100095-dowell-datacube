import os
from django.conf import settings
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = "mongodb://localhost:27017/"
AUTH_DB_NAME = "datacube_V2_auth"

class MongoConnection:
    def __init__(self):
        self.client = MongoClient(MONGODB_URI)
        self.db = self.client[AUTH_DB_NAME]

    def get_collection(self, collection_name):
        return self.db[collection_name]

# Instantiate the connection
mongo_conn = MongoConnection()