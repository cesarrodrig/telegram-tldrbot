import os
import logging
import pytz

BOT_URL = os.getenv("BOT_URL", "")
ENVIRONMENT = os.getenv("ENVIRONMENT", "local")
WEBHOOK = os.getenv("WEBHOOK", "")
BOTTLE_PORT = os.getenv("BOTTLE_PORT", "8080")
BOTTLE_HOST = os.getenv("BOTTLE_HOST", "127.0.0.1")
LAST_UPDATE_ID_FILE = "last_update"
GROUPS_DB_NAME = "tags"
POLL_PERIOD = 1
MAX_TAGS = 5
LOGGING_LEVEL = logging.DEBUG
LOCAL_TIMEZONE = pytz.timezone('America/Mexico_City')
PENDING_MIGRATION = os.getenv("PENDING_MIGRATION", False)
