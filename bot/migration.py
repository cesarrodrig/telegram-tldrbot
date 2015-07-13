import json
import jsonpickle

from chat import Chat
from tag import Tag
from user import User
from config import *


def do():
    f = open(CHATS_COLLECTION_NAME)
    tags = json.loads(f.read())
    f.close()

    chats_by_id = {}
    for id, tags_json in tags.items():
        tags = []
        for j in tags_json:
            user_json = j["from"]
            first_name = user_json.get("first_name", "")
            last_name = user_json.get("last_name", "")
            username = user_json.get("username", "")
            user = User(user_json["id"], first_name, last_name, username)
            tag = Tag(j["text"], user, j["date"])
            tags.append(tag)

        admin = 58699815
        chats_by_id[id] = Chat(id, tags=tags, admin=admin)

    encoded = jsonpickle.encode(chats_by_id)

    f = open(CHATS_COLLECTION_NAME, "w")
    f.write(encoded)
    f.close()

