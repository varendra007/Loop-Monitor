import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL")
STATUS_PATH = os.getenv("STATUS_PATH")
TIMEZONE_PATH = os.getenv("TIMEZONE_PATH")
HOURS_PATH = os.getenv("HOURS_PATH")
PING_PERIOD_MINS = int(os.getenv("PING_PERIOD_MINS"))
HARD_CODE_TIME = os.getenv("HARD_CODE_TIME")
