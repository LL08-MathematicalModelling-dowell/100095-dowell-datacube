import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB_NAME = os.getenv("AUTH_DB_NAME")

class MongoConnection:
    def __init__(self):
        self.client = MongoClient(MONGO_URI)
        self.db = self.client[MONGO_DB_NAME]

    def get_collection(self, collection_name):
        return self.db[collection_name]

# Instantiate the connection
mongo_conn = MongoConnection()