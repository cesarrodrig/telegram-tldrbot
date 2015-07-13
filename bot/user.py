
def user_from_json(user_json):
    first_name = user_json.get("first_name", "")
    last_name = user_json.get("last_name", "")
    username = user_json.get("username", "")
    user = User(user_json["id"], first_name, last_name, username)
    return user

class User(object):

    def __init__(self, id, first_name="", last_name="", username=""):
        self.id = str(id)
        self.first_name = first_name
        self.last_name = last_name
        self.username = username
        self.last_tldr = None

    def pretty_print(self):
        username = self.username if self.username else self.first_name
        return username
