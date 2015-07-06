import user

def message_from_json(j):
    id = j["message_id"]
    u = user.user_from_json(j["from"])
    date = j["date"]
    chat_id = j["chat"]["id"]
    text = j.get("text", "")
    return Message(id, u, date, chat_id, text)

class Message(object):
    def __init__(self, id, user, date, chat_id, text=""):
        self.id = id
        self.user = user
        self.date = date
        self.chat_id = str(chat_id)
        self.text = text
