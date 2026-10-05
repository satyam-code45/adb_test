import os

from pymongo import MongoClient

mongo_uri = f"mongodb://{os.environ['MONGO_HOST']}:{os.environ['MONGO_PORT']}"

# Fail fast instead of pymongo's 30s default when mongo is down
client = MongoClient(mongo_uri, tz_aware=True, serverSelectionTimeoutMS=3000)
db = client['test_db']
