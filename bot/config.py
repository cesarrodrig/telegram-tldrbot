import os
import logging
import pytz

BOT_URL = os.getenv("BOT_URL", "")
BOT_CHAT_ID = "58699815"
ENVIRONMENT = os.getenv("ENVIRONMENT", "local")
WEBHOOK = os.getenv("WEBHOOK", "")
BOTTLE_PORT = os.getenv("BOTTLE_PORT", "8080")
BOTTLE_HOST = os.getenv("BOTTLE_HOST", "127.0.0.1")
LAST_UPDATE_ID_FILE = "last_update"
CHATS_COLLECTION_NAME = "chats"
USERS_COLLECTION_NAME = "users"
POLL_PERIOD = 1
MAX_TAGS = 5
LOGGING_LEVEL = logging.DEBUG
LOCAL_TIMEZONE = pytz.timezone('America/Mexico_City')
PENDING_MIGRATION = os.getenv("PENDING_MIGRATION", False)
DATABASE_URL = os.getenv("DATABASE_URL", "http://cesar@localhost:5432/ehbot")
