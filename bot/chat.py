
class Chat(object):

    def __init__(self, id, name="", tags=[], admin=None):
        self.id = str(id)
        self.name = name
        self.tags = tags
        self.admin = admin
