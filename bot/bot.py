import json
import time
import datetime
import logging

from config import *
from requester import GetUpdatesRequest
from requester import SendMessageRequest
from tag import Tag


HELP = """
TlDrBot saves tags so important topics can be retrieved later by users without having to read all the conversation.

To add a tag, mention the @TlDrBot followed by the tag:

@TlDrBot dinner at 8:30pm

Or use the /tag command.

Commands:

/chatid - Returns the ID of the current chat.
/tldr <chat_id> - Gets the tags from a chat. <chat_id> is optional and defaults to the current chat.
/tag <text> - Adds a tag to the current chat.

"""
BOT_TAG = "@tldrbot"

class TlDrBot:

    def __init__(self):
        update_id = "0"
        try:
            f = open(LAST_UPDATE_ID_FILE)
            update_id = f.read().split('\n')[0]
            f.close()
        except:
            pass

        tags = {}
        try:
            f = open(TAGS_FILE)
            tags = json.loads(f.read())
            f.close()
        except:
            pass

        self.tags = tags
        self.last_update_id = int(update_id)
        self.logger = logging.getLogger(__name__)

    def start(self):
        while True:
            self.poll()
            time.sleep(POLL_PERIOD)

    def poll(self):
        request = GetUpdatesRequest(offset = self.last_update_id)
        response, content = request.do()
        if response.status_code != 200 or not content["ok"]:
            raise "Failed to get updates", response.text

        messages = self.get_messages(content)
        last_update_id = self.get_last_update_id(content)
        self.process_messages(messages)

        self.save_tags()
        self.save_last_update_id(last_update_id)

    def get_messages(self, json):
        return [m["message"] for m in json["result"]]

    def get_last_update_id(self, json):
        return json["result"][-1]["update_id"] if json["result"] else None

    def process_messages(self, messages):

        for message in messages:
            chat_id = str(message["chat"]["id"])
            if message["text"] == "/help":
                self.process_help(chat_id)

            elif message["text"].lower().find("/tldr") == 0:
                self.process_tldr_query(chat_id, message["text"])

            elif message["text"].lower().find("/chatid") == 0:
                self.process_chat_id_query(chat_id)

            elif message["text"].lower().find("/tag") == 0:
                self.process_tag_command(message)

            elif BOT_TAG in message["text"].lower():
                self.process_tag_mention(message)

    def process_help(self, chat_id):
        request = SendMessageRequest(chat_id, HELP)
        response, content = request.do()
        if response.status_code != 200 or not content["ok"]:
            raise "Failed to send /help"

    def process_tag_command(self, message):
        chat_id = str(message["chat"]["id"])
        tag = self.get_tag_from_message(message, lambda text: text.split("/tag")[-1].strip())
        self.add_tag(chat_id, tag)

    def process_tag_mention(self, message):
        """
        Takes a message that mentions TlDrBot and stores it as a tag
        """
        chat_id = str(message["chat"]["id"])
        tag = self.get_tag_from_message(message, self.get_tag_text_from_mention)
        self.add_tag(chat_id, tag)

    def process_chat_id_query(self, chat_id):
        text = "This chat's ID: {}\nUse it to call '/tldr {}'".format(chat_id, chat_id)
        request = SendMessageRequest(chat_id, text)
        response, content = request.do()
        if response.status_code != 200 or not content["ok"]:
            raise "Failed to send /help"

    def process_tldr_query(self, chat_id, text):
        query_chat = text.split("/tldr")[-1].strip()
        query_chat_id = None
        if not query_chat:
            query_chat_id = chat_id
        else:
            # query_chat_id = self.get_chat_id_from_chat_name(query_chat)
            query_chat_id = query_chat

        self.send_tags(chat_id, query_chat_id)

    def send_tags(self, chat_id, query_chat_id):
        tags = []
        tags_text = ""
        if query_chat_id in self.tags:
            tags = self.tags[query_chat_id]
            tags_text = "\n- ".join([self.tag_to_text(t) for t in tags])
            tags_text = "Tags for chat {}:\n- {}".format(chat_id, tags_text)
        else:
            tags_text = "No Tags found for this chat"

        request = SendMessageRequest(chat_id, tags_text)
        response, content = request.do()
        if response.status_code != 200 or not content["ok"]:
            raise "Failed to send /tldr"

    def add_tag(self, chat_id, tag):
        if chat_id not in self.tags:
            self.tags[chat_id] = []
        elif len(self.tags[chat_id]) >= 5:
            self.tags[chat_id].pop(0)

        self.tags[chat_id].append(tag)

    def save_last_update_id(self, last_update_id):
        # if we found results, increment the last_update_id, else it stays the same
        if not last_update_id:
            return

        self.last_update_id = last_update_id + 1
        f = open(LAST_UPDATE_ID_FILE, "w")
        f.write(str(self.last_update_id))
        f.close()

    def save_tags(self):
        f = open(TAGS_FILE, "w")
        f.write(json.dumps(self.tags))
        f.close()

    def get_tag_from_message(self, message, tag_func):
        tag = {
            "from" : message["from"],
            "date" : message["date"],
            "text" : tag_func(message["text"])
        }
        return tag

    def get_tag_text_from_mention(self, text):
        return text[text.lower().find(BOT_TAG) + len(BOT_TAG):].strip()

    def tag_to_text(self, tag):
        # date = datetime.datetime.fromtimestamp(tag["date"]).strftime('%Y-%m-%d %H:%M:%S')
        return '"{}" @{}'.format(tag["text"], tag["from"]["username"])

bot = TlDrBot()
bot.start()
