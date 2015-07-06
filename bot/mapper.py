import jsonpickle

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

    def get_chat_by_id(self, id):
        return self.chats.get(id)

    def save_chat(self, chat):
        self.chats[chat.id] = chat
        f = open(self.db_name, "w")
        f.write(jsonpickle.encode(self.chats))
        f.close()
