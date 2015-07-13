import urlparse

import jsonpickle
import psycopg2

from config import *

CREATE_TABLE = "CREATE TABLE %s (id varchar(20) PRIMARY KEY, value text);"

SELECT_BY_ID = "SELECT * FROM {} WHERE id=%(id)s;"
INSERT = "INSERT INTO {} VALUES (%(id)s, %(value)s);"
UPDATE_BY_ID = "UPDATE {} SET value=%(value)s WHERE id=%(id)s;"

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

def db_operation(func):
    def inner(self, *args, **kwargs):
        opened_conn = bool(not self.connection or self.connection.closed)
        self.connection = self.connect()
        self.cursor = self.connection.cursor()
        try:
            return func(self, *args, **kwargs)
        except psycopg2.DatabaseError as e:
            raise e
        finally:
            # don't close a connection you didn't open
            if self.connection and opened_conn:
                self.connection.close()
                self.connection = None

    return inner

class PostgreSQLMapper(Mapper):

    def __init__(self, db_name):
        super(PostgreSQLMapper, self).__init__(db_name)
        self.url = urlparse.urlparse(DATABASE_URL)
        self.connection = None

        self.provision_db()

    def connect(self):
        if self.connection and not self.connection.closed: return self.connection
        conn = psycopg2.connect(
            database=self.url.path[1:],
            user=self.url.username,
            password=self.url.password,
            host=self.url.hostname,
            port=self.url.port
        )
        conn.set_session(autocommit=True)
        self.connection = conn

        return conn

    @db_operation
    def provision_db(self):
        try:
            self.cursor.execute(CREATE_TABLE, CHATS_COLLECTION_NAME)
            self.cursor.execute(CREATE_TABLE, USERS_COLLECTION_NAME)
        except:
            pass # ignore errors

    def get_chat_by_id(self, id):
        res = self._select_by_id(CHATS_COLLECTION_NAME, {'id': id })
        if not res:
            return None

        return jsonpickle.decode(res[1])

    def save_chat(self, chat):
        blob = jsonpickle.encode(chat)
        if self.get_chat_by_id(chat.id): # update chat if it already exists
            self._update_by_id(CHATS_COLLECTION_NAME, {'id': chat.id, 'value': blob})
        else:
            self._insert(CHATS_COLLECTION_NAME, {'id': chat.id, 'value': blob})

    def get_user_by_id(self, id):
        res = self._select_by_id(USERS_COLLECTION_NAME, {'id': id })
        if not res:
            return None

        return jsonpickle.decode(res[1])

    def save_user(self, user):
        blob = jsonpickle.encode(user)
        if self.get_chat_by_id(user.id): # update user if it already exists
            self._update_by_id(USERS_COLLECTION_NAME, {'id': user.id, 'value': blob})
        else:
            self._insert(USERS_COLLECTION_NAME, {'id': user.id, 'value': blob})

    @db_operation
    def _select_by_id(self, table, values):
        statement = SELECT_BY_ID.format(table)
        self.cursor.execute(statement, values)
        return self.cursor.fetchone()

    @db_operation
    def _insert(self, table, values):
        statement = INSERT.format(table)
        self.cursor.execute(statement, values)

    @db_operation
    def _update_by_id(self, table, values):
        statement = UPDATE_BY_ID.format(table)
        self.cursor.execute(statement, values)
