import pymongo
from dotenv import load_dotenv
from config.constants import MONGO_URL

load_dotenv()


client = pymongo.MongoClient(MONGO_URL)
db = client["LoopMonitor"]
