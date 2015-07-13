import json
import time
import sys
import traceback
from datetime import datetime

import bottle

import logger
import migration
from chat import Chat
from message import Message
from message import message_from_json
from tag import Tag
from mapper import PostgreSQLMapper
from config import *
from requester import GetUpdatesRequest
from requester import SendMessageRequest
from requester import SetWebhookRequest


HELP = """
EhBot saves tags so important topics can be retrieved later by users without having to read all the conversation.

To add a tag, mention the @EhBot followed by the tag:

@EhBot dinner at 8:30pm

Or use the /tag command.

Commands:

/chatid - Returns the ID of the current chat.
/tldr <chat_id> - Gets the tags from a chat. <chat_id> is optional and defaults to the current chat. If /tldr is sent without <chat_id> and as a private message to @EhBot, it will reply with your last requested /tldr chat.
/tag <text> - Adds a tag to the current chat.
/deletetag <num> <chat_id> - Deletes tag from a chat. <num> should be a tag that you own. <chat_id> is optional and defaults to the current chat.
"""
BOT_TAG = "@ehbot"

class EhBot:

    def __init__(self):
        if PENDING_MIGRATION:
            migration.do()

        update_id = "0"
        try:
            f = open(LAST_UPDATE_ID_FILE)
            update_id = f.read().split('\n')[0]
            f.close()
        except:
            pass

        self.mapper = PostgreSQLMapper(CHATS_COLLECTION_NAME)
        self.last_update_id = int(update_id)
        self.logger = logger.get_logger(__name__)

    def start(self):
        if ENVIRONMENT == "heroku":
            self.run_webhook()
        else:
            self.run_poll()

    def run_webhook(self):
        if not WEBHOOK or not BOTTLE_PORT:
            raise InvalidWebhookException("Webhook is empty")

        request = SetWebhookRequest(url=WEBHOOK)
        response, content = request.do()
        if response.status_code != 200 or not content["ok"]:
            raise InvalidWebhookException("Telegram response: %s" % content)

        self._app = bottle.Bottle()
        self.map_routes()
        self._app.run(host=BOTTLE_HOST, port=sys.argv[1])

    def map_routes(self):
        self._app.route("/", method="POST", callback=self.handle_push_notification)
        self._app.route("/", method="GET", callback=self.handle_health)

    def run_poll(self):
        # disabling webhook
        request = SetWebhookRequest(url="")
        response, content = request.do()
        if response.status_code != 200 or not content["ok"]:
            raise InvalidWebhookException("Telegram response: %s" % content)

        while True:
            try:
                self.poll()
            except Exception as e:
                self.logger.error(str(traceback.format_exc()))
                self.logger.error(e)

            time.sleep(POLL_PERIOD)

    def poll(self):
        request = GetUpdatesRequest(offset = self.last_update_id)
        response, content = request.do()
        if response.status_code != 200 or not content["ok"]:
            raise GetUpdatesException("Failed to get updates")

        self.process_updates(content["result"])

    def handle_health(self):
        return "I'm fine"

    def handle_push_notification(self):
        try:
            content = json.load(bottle.request.body)
            self.logger.info("Loaded from webhook: %s" % content)
            self.process_update(content)
        except Exception as e:
            self.logger.error(str(traceback.format_exc()))
            self.logger.error(e)

    def get_messages(self, results):
        return [message_from_json(m["message"]) for m in results if "message" in m]

    def get_last_update_id(self, results):
        return results[-1]["update_id"] if results else None

    def process_updates(self, updates):
        messages = self.get_messages(updates)
        last_update_id = self.get_last_update_id(updates)
        self.process_messages(messages)

        self.save_last_update_id(last_update_id)

    def process_update(self, update_json):
        message = message_from_json(update_json["message"])
        self.process_messages([message])

    def process_messages(self, messages):

        for message in messages:
            chat_id = message.chat_id
            text = message.text
            if not text:
                continue

            if text == "/help":
                self.process_help(chat_id)

            elif text.lower().find("/tldr") == 0:
                self.process_tldr_query(message)

            elif text.lower().find("/chatid") == 0:
                self.process_chat_id_query(chat_id)

            elif text.lower().find("/tag ") == 0:
                self.process_tag_command(message)

            elif text.lower().find("/deletetag ") == 0:
                self.process_delete_tag_command(message)

            elif BOT_TAG in text.lower():
                self.process_tag_mention(message)

    def process_help(self, chat_id):
        request = SendMessageRequest(chat_id, HELP)
        response, content = request.do()
        if response.status_code != 200 or not content["ok"]:
            raise "Failed to send /help"

    def process_tag_command(self, message):
        chat_id = message.chat_id
        try:
            tag = self.get_tag_from_message(message, lambda text: text.split("/tag")[-1].strip())
            self.add_tag(chat_id, tag)
        except UserTagLimitException as e:
            self.send_warning_to_user(message.user.id, "Stop spamming")
            self.logger.warn(e.message)

    def process_tag_mention(self, message):
        """
        Takes a message that mentions EhBot and stores it as a tag
        """
        chat_id = message.chat_id
        try:
            tag = self.get_tag_from_message(message, self.get_tag_text_from_mention)
            self.add_tag(chat_id, tag)
        except UserTagLimitException as e:
            self.send_warning_to_user(message.user.id, "Stop spamming")
            self.logger.warn(e.message)

    def process_chat_id_query(self, chat_id):
        text = "This chat's ID: {}\nUse it to call '/tldr {}'".format(chat_id, chat_id)
        request = SendMessageRequest(chat_id, text)
        response, content = request.do()
        if response.status_code != 200 or not content["ok"]:
            raise "Failed to send /help"

    def process_tldr_query(self, message):
        # try to get it from DB
        user = self.mapper.get_user_by_id(message.user.id)
        if not user: user = message.user

        query_chat = message.text.split("/tldr")[-1].strip()
        query_chat_id = None

        if query_chat: # chat id specified
            query_chat_id = query_chat
            user.last_tldr = query_chat_id
        elif message.chat_id == BOT_CHAT_ID and user.last_tldr:
            # sent directly to ehbot, try to provide last tldr
            query_chat_id = user.last_tldr
        else: # no query chat or tldr, provide current chat tldr
            query_chat_id = message.chat_id
            user.last_tldr = query_chat_id

        self.send_tags(user.id, query_chat_id)
        self.mapper.save_user(user)

    def process_delete_tag_command(self, message):
        chat_id = message.chat_id
        command = message.text.split(" ")
        tag_num = command[1]
        if len(command) >= 3:
            chat_id = command[2]

        if not tag_num.isdigit():
            self.send_warning_to_user(user_id, "Tag number is not valid")

        tag_num = int(tag_num) - 1

        user_id = message.user.id
        chat = self.mapper.get_chat_by_id(chat_id)
        if not chat:
            self.send_warning_to_user(user_id, "Chat doesn't have any tags")
        elif tag_num < 0 or tag_num >= len(chat.tags):
            self.send_warning_to_user(user_id, "Tag number is out of range")
        elif chat.tags[tag_num].user.id != user_id:
            # owns the tag?
            self.send_warning_to_user(user_id, "This tag is not yours")
        else:
            tag = chat.tags.pop(tag_num)
            self.send_warning_to_user(user_id, "Tag '%s' deleted" % tag.text)

    def send_tags(self, chat_id, query_chat_id):
        tags_text = ""
        chat = self.mapper.get_chat_by_id(query_chat_id)
        if not chat or len(chat.tags) == 0:
            tags_text = "No Tags found for this chat"
        else:
            tags = ["%s. %s" % (i+1, t.pretty_print()) for i, t in enumerate(chat.tags)]
            tags_text = "\n".join(tags)
            tags_text = "Tags for chat %s:\n%s" % (query_chat_id, tags_text)

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
        chat = self.mapper.get_chat_by_id(chat_id)
        if not chat:
            chat = Chat(chat_id)
        elif len(chat.tags) >= 5:
            chat.tags.pop(0)

        chat.tags.append(tag)
        self.mapper.save_chat(chat)

    def save_last_update_id(self, last_update_id):
        # if we found results, increment the last_update_id, else it stays the same
        if not last_update_id:
            return

        self.last_update_id = last_update_id + 1
        f = open(LAST_UPDATE_ID_FILE, "w")
        f.write(str(self.last_update_id))
        f.close()

    def get_tag_from_message(self, message, tag_func):
        date = datetime.fromtimestamp(message.date)
        chat_id = message.chat_id
        user = message.user

        chat = self.mapper.get_chat_by_id(chat_id)
        if chat:
            for t in chat.tags:
                d = datetime.fromtimestamp(t.date)

                if t.user.id == user.id and (message.date - t.date) <= 5 * 60:
                    username = t.user.pretty_print()
                    raise UserTagLimitException("User '%s' is submitting too rapidly" % username)
        text = tag_func(message.text)
        return Tag(text=text, user=user, date=message.date)

    def get_tag_text_from_mention(self, text):
        return text[text.lower().find(BOT_TAG) + len(BOT_TAG):].strip()

class UserTagLimitException(Exception):
    pass

class GetUpdatesException(Exception):
    pass

class InvalidWebhookException(Exception):
    pass

bot = EhBot()
bot.start()
