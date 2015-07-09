import jsonpickle

from config import *

class Mapper(object):

    def __init__(self, db_name):
        self.db_name = db_name

class TextFileMapper(Mapper):

    def __init__(self, db_name):
        super(TextFileMapper, self).__init__(db_name)
        self.chats = {}
        try:
            f = open(self.db_name)
            self.chats = jsonpickle.decode(f.read())
            f.close()
        except:
            pass

        self.users = {}
        try:
            f = open(USERS_COLLECTION_NAME)
            self.users = jsonpickle.decode(f.read())
            f.close()
        except:
            pass

    def get_chat_by_id(self, id):
        return self.chats.get(id)

    def get_user_by_id(self, id):
        return self.users.get(id)

    def save_chat(self, chat):
        self.chats[chat.id] = chat
        f = open(self.db_name, "w")
        f.write(jsonpickle.encode(self.chats))
        f.close()

    def save_user(self, user):
        self.users[user.id] = user
        f = open(USERS_COLLECTION_NAME, "w")
        f.write(jsonpickle.encode(self.users))
        f.close()
