from pymongo import MongoClient
from config import Config

client = MongoClient(Config.MONGO_URI)
db = client["zero_hunger"]

users_collection = db.users
foods_collection = db.foods
