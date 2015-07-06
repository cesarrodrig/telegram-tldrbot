from datetime import datetime

from config import *

class Tag(object):

    def __init__(self, text, user, date):
        self.text = text
        self.user = user
        self.date  = date

    def pretty_print(self):
        date = datetime.fromtimestamp(self.date, tz=LOCAL_TIMEZONE).strftime('%a %d %I:%M%p')
        username = self.user.pretty_print()
        return '"%s" @%s %s' % (self.text, username, date)
