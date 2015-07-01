import json
import time
from datetime import datetime

import logger
from config import *
from requester import GetUpdatesRequest
from requester import SendMessageRequest


HELP = """
EhBot saves tags so important topics can be retrieved later by users without having to read all the conversation.

To add a tag, mention the @EhBot followed by the tag:

@EhBot dinner at 8:30pm

Or use the /tag command.

Commands:

/chatid - Returns the ID of the current chat.
/tldr <chat_id> - Gets the tags from a chat. <chat_id> is optional and defaults to the current chat.
/tag <text> - Adds a tag to the current chat.
/deletetag <num> <chat_id> - Deletes tag from a chat. <num> should be a tag that you own. <chat_id> is optional and defaults to the current chat.
"""
BOT_TAG = "@ehbot"

class EhBot:

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
        self.logger = logger.get_logger(__name__)

    def start(self):
        while True:
            self.poll()
            time.sleep(POLL_PERIOD)

    def poll(self):
        request = GetUpdatesRequest(offset = self.last_update_id)
        response, content = request.do()
        if response.status_code != 200 or not content["ok"]:
            raise GetUpdatesException("Failed to get updates")

        messages = self.get_messages(content)
        last_update_id = self.get_last_update_id(content)
        self.process_messages(messages)

        self.save_tags()
        self.save_last_update_id(last_update_id)

    def get_messages(self, json):
        return [m["message"] for m in json["result"] if "message" in m]

    def get_last_update_id(self, json):
        return json["result"][-1]["update_id"] if json["result"] else None

    def process_messages(self, messages):

        for message in messages:
            chat_id = str(message["chat"]["id"])
            user_id = str(message["from"]["id"])
            if "text" not in message:
                continue

            if message["text"] == "/help":
                self.process_help(chat_id)

            elif message["text"].lower().find("/tldr") == 0:
                self.process_tldr_query(chat_id, user_id, message["text"])

            elif message["text"].lower().find("/chatid") == 0:
                self.process_chat_id_query(chat_id)

            elif message["text"].lower().find("/tag") == 0:
                self.process_tag_command(message)

            elif message["text"].lower().find("/deletetag") == 0:
                self.process_delete_tag_command(message)

            elif BOT_TAG in message["text"].lower():
                self.process_tag_mention(message)

    def process_help(self, chat_id):
        request = SendMessageRequest(chat_id, HELP)
        response, content = request.do()
        if response.status_code != 200 or not content["ok"]:
            raise "Failed to send /help"

    def process_tag_command(self, message):
        chat_id = str(message["chat"]["id"])
        try:
            tag = self.get_tag_from_message(message, lambda text: text.split("/tag")[-1].strip())
            self.add_tag(chat_id, tag)
        except UserTagLimitException as e:
            self.send_warning_to_user(message["from"]["id"], "Stop spamming")
            self.logger.warn(e.message)

    def process_tag_mention(self, message):
        """
        Takes a message that mentions EhBot and stores it as a tag
        """
        chat_id = str(message["chat"]["id"])
        try:
            tag = self.get_tag_from_message(message, self.get_tag_text_from_mention)
            self.add_tag(chat_id, tag)
        except UserTagLimitException as e:
            self.send_warning_to_user(message["from"]["id"], "Stop spamming")
            self.logger.warn(e.message)

    def process_chat_id_query(self, chat_id):
        text = "This chat's ID: {}\nUse it to call '/tldr {}'".format(chat_id, chat_id)
        request = SendMessageRequest(chat_id, text)
        response, content = request.do()
        if response.status_code != 200 or not content["ok"]:
            raise "Failed to send /help"

    def process_tldr_query(self, chat_id, user_id, text):
        query_chat = text.split("/tldr")[-1].strip()
        query_chat_id = None
        if not query_chat:
            query_chat_id = chat_id
        else:
            # query_chat_id = self.get_chat_id_from_chat_name(query_chat)
            query_chat_id = query_chat

        self.send_tags(user_id, query_chat_id)

    def process_delete_tag_command(self, message):
        chat_id = str(message["chat"]["id"])
        command = message["text"].split(" ")
        tag_num = command[1]
        if len(command) >= 3 and command[2].isdigit():
            chat_id = command[2]

        if not tag_num.isdigit():
            self.send_warning_to_user(user_id, "Tag number is not valid")

        tag_num = int(tag_num) - 1

        user_id = message["from"]["id"]
        if chat_id not in self.tags:
            self.send_warning_to_user(user_id, "Chat doesn't have any tags")
        elif tag_num > len(self.tags[chat_id]):
            self.send_warning_to_user(user_id, "Tag number is not valid")
        elif self.tags[chat_id][int(tag_num)]["from"]["id"] != message["from"]["id"]:
            # owns the tag?
            self.send_warning_to_user(user_id, "This tag is not yours")
        else:
            self.tags[chat_id].pop(tag_num)
            self.send_warning_to_user(user_id, "Tag deleted")

    def send_tags(self, chat_id, query_chat_id):
        tags = []
        tags_text = ""
        if query_chat_id in self.tags:
            tags = self.tags[query_chat_id]
            tags = ["%s. %s" % (i+1, self.tag_to_text(t)) for i, t in enumerate(tags)]
            tags_text = "\n".join(tags)
            tags_text = "Tags for chat %s:\n%s" % (query_chat_id, tags_text)
        else:
            tags_text = "No Tags found for this chat"

        request = SendMessageRequest(chat_id, tags_text)
        response, content = request.do()
        if response.status_code != 200 or not content["ok"]:
            raise "Failed to send /tldr"

    def send_warning_to_user(self, user_id, warning_text):
        request = SendMessageRequest(user_id, warning_text)
        response, content = request.do()
        if response.status_code != 200 or not content["ok"]:
            raise "Failed to send warning to user"

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
        date = datetime.fromtimestamp(message["date"])
        chat_id = str(message["chat"]["id"])
        user_id = message["from"]["id"]

        if chat_id in self.tags:
            for tag in self.tags[chat_id]:
                d = datetime.fromtimestamp(tag["date"])

                if tag["from"]["id"] == user_id and (date - d).days == 0 and (date - d).seconds <= 5 * 60:
                    username = self.get_user_from_source(tag["from"])
                    raise UserTagLimitException("User '%s' is submitting too rapidly" % username)

        tag = {
            "from" : message["from"],
            "date" : message["date"],
            "text" : tag_func(message["text"])
        }
        return tag

    def get_tag_text_from_mention(self, text):
        return text[text.lower().find(BOT_TAG) + len(BOT_TAG):].strip()

    def tag_to_text(self, tag):
        date = datetime.fromtimestamp(tag["date"], tz=LOCAL_TIMEZONE).strftime('%a %d %I:%M%p')
        username = self.get_user_from_source(tag["from"])
        return '"%s" @%s %s' % (tag["text"], username, date)

    def get_user_from_source(self, source):
        username = source["username"] if "username" in source else source["first_name"]
        return username

class UserTagLimitException(Exception):
    pass

class GetUpdatesException(Exception):
    pass

bot = EhBot()
bot.start()
