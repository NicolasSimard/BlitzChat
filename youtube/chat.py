""" chat module defines all the classes and auxilary functions to work with
youtube chats.

The classes are:

    ChatMessage             Represents a chat message
    Chat                    Represents a general chat, with its messages
    LiveChat(Thread)        Represents a chat associated with a youtube service
    MockChat(Thread)        Represents a chat constructed from a file

The auxilary functions are:

"""

from apiclient.errors import HttpError
import threading
import datetime
import time
from dateutil.parser import parse as dateparser
import json
import re
import os

LIVECHAT_BACKUP_DIR = "livechat-backup"

def timestamp():
    now = datetime.datetime.now().time().replace(microsecond = 0).__str__()
    now = now.replace(":","") # : is not allowed in windows file names.
    return now

def datetimestamp():
    now = datetime.datetime.now().replace(microsecond = 0).__str__()
    now = now.replace(":","").replace(" ","_") # : is not allowed in windows file names.
    return now

class ChatMessage:
    """ A ChatMessage object represents a message in a Chat.

    Attributes:
        author              Author of the message.
        published_at        Moment at which the message was published.
        content             Text content of the message.
        labels              A list of labels (strings) attached by classifiers.
    """

    def __init__(self, **kwargs):
        """ The __init__ function takes only keyword arguments. There are two
        possible combinations:

        1) corresponding to the dictionary ChatMessage.__dict__:
        {
            "author": str,
            "published_at": str,
            "content": str
            "labels": [
                str
            ]
        }

        2) corresponding to the dictionary which represents the snippet dict of
        a "youtube#liveChatMessage" ressource in a youtube live chat:
        {
            "type": "textMessageEvent",
            "liveChatId": "Cg0KC1lxVHZfaC1CempZ",
            "authorChannelId": "UC7aeSVebvKLp4o5MLtq5LZg",
            "publishedAt": "2018-01-09T21:52:33.028Z",
            "hasDisplayContent": true,
            "displayMessage": "Allo",
            "textMessageDetails": {
                "messageText": "Allo"
            }
        }

        Raises a RuntimeError if the author, publication time or content is missing.
        """

        if "authorChannelId" in kwargs:
            self.author = kwargs["authorChannelId"]
        elif "author" in kwargs:
            self.author = kwargs["author"]
        else:
            raise RuntimeError("No author provided.")

        if "publishedAt" in kwargs:
            self.published_at = kwargs["publishedAt"]
        elif "published_at" in kwargs:
            self.published_at = kwargs["published_at"]
        else:
            raise RuntimeError("No publication moment provided.")

        if "textMessageDetails" in kwargs:
            self.content = kwargs["textMessageDetails"]["messageText"]
        elif "content" in kwargs:
            self.content = kwargs["content"]
        else:
            raise RuntimeError("No content provided.")

        self.labels = kwargs.get("labels", [])

    def add_label(self, label):
        """ Add a label (a string) to the chat message. """

        self.labels.append(label)

    def as_dict(self):
        """ Returns the following dictionary:
         {
            "author": str,
            "published_at": str,
            "content": str
            "labels": [
                str
            ]
        }
        """

        return dict([
            ("author", self.author),
            ("published_at", self.published_at),
            ("content", self.content),
            ("labels", self.labels)
        ])

    def __repr__(self):
        """ Returns self.as_dict(). """
        return self.as_dict().__str__()

    def __str__(self):
        # Try to know when the message was published
        try:
            published_time = dateparser(self.published_at).time().replace(microsecond=0)
        except ValueError as e:
            published_time = self.published_at

        return "{} {:15s} at {}: {}".format(
            ", ".join(self.labels),
            self.author,
            published_time,
            self.content
        )


class Chat:
    """ A Chat object represents a collection of messages which can vary in time.

    Attributes:
        lock                A threading.Lock object to lock the object

    Methods:
        append_messages     Append messages to the object's messages
        get_messages        Return chat messages
        extend_messages     Extend the list of messages
        save_to_json        Save Chat object to JSON format using its representation
    """

    lock = threading.RLock()

    def __init__(self):
        self._messages = []

    def append_message(self, message):
        if isinstance(message, ChatMessage):
            self._messages.append(message) # append is thread-safe
        else:
            print(">>> Unable to append {} to Chat object.".format(message))

    def get_messages(self, begin, end):
        return self._messages[begin: end]

    def extend_messages(self, messages):
        for message in messages:
            self.append_message(message)

    def save_to_json(self, base_dir, file_name=None):
        """ Save to file named file_name in base_dir. If file_name=None (default)
        the file name will be 'chat_session_hhmmss.json'.

        It is always a good idea to test this function BEFORE running the actual
        chat session to make sure that the data will be saved after the session.
        For example, one could do
        Chat().save_to_json(CURRENT_SAVE_DIR, file_name="test_save.txt")
        """

        if file_name is None:
            now = datetime.datetime.now().time().replace(microsecond = 0).__str__()
            now = now.replace(":","") # : is not allowed in windows file names.
            file_name = "chat_session_{}.json".format(now)
        file_name = os.path.join(base_dir, file_name)

        json_object = [message.as_dict() for message in self._messages]

        try:
            with open(file_name, 'w') as f:
                json.dump(json_object, f, indent=4)
        except Exception as e:
            print(">>> There was a problem with saving the chat object.")
            print(e)

    def __repr__(self):
        return dict([
            ("messages", [message.__repr__() for message in self._messages])
        ]).__str__()

    def __str__(self):
        return("Chat object containing {} messages. ".format(len(self._messages)))


class MockChat(threading.Thread):
    """ A MockChat object represents a mock chat, i.e. a reproduction of a live
    chat from a saved list of messages.

    Attributes:
        has_new_messages    A threading.Condition object that notifies all the
                            waiting threads when new messages are available.
        is_over             A threading.Event object that is set when the chat
                            is over.
        start_time          The time at which the chat started. This is the
                            moment where the first message of the chat was posted.
        refresh_rate        The refreshing rate of the Chat.

    Methods:
        start               Start the chat.
        estimated_duration  Estimated duration of the mock chat.
    """

    index = 0
    is_over = threading.Event()
    has_new_messages = threading.Condition()

    def __init__(self, arch_mess, chat, refresh_rate, speed=1):
        """ A mock chat is an object constructed from a list of ChatMessage
        whose purpose is to re-create the chat thread.

        The constructor takes a list of ChatMessage objects and a refresh rate.
        The refresh rate is the frequency at which the chat checks if new
        chat messages are available. If speed is an integer different from one, play
        the chat at speed times the speed.
        """

        threading.Thread.__init__(self, name="Mock chat.")
        self.chat = chat
        self._arch_mess = arch_mess
        try:
            self.start_time = dateparser(arch_mess[0].published_at)
        except IndexError:
            print("No messages in MockChat.")
        if isinstance(speed, int):
            self.speed = speed
        else:
            self.speed = 1
        self.refresh_rate = refresh_rate
        self.nbr_messages = len(arch_mess)

    def estimated_duration(self):
        """ How long should the mock chat last, given its speed."""

        span = (dateparser(self._arch_mess[-1].published_at)
                - dateparser(self._arch_mess[0].published_at)).total_seconds()
        return span / self.speed

    def run(self):
        """ As the time passes, more messages are available in the MockChat.
        The run method makes those messages available (by putting them in
        self.chat) and notifies all waiting threads via its has_new_messages
        condition.
        """

        actual_start_time = datetime.datetime.now()

        while not self.is_over.is_set():
            delta = datetime.datetime.now() - actual_start_time
            delta *= self.speed # Accelerate time

            old_index = self.index
            while self.index < self.nbr_messages \
                and dateparser(self._arch_mess[self.index].published_at) < (self.start_time + delta):
                self.index += 1

            if self.index == self.nbr_messages:
                self.is_over.set()

            if old_index < self.index:
                self.chat.extend_messages(self._arch_mess[old_index: self.index])
                with self.has_new_messages:
                    self.has_new_messages.notify_all()

            time.sleep(self.refresh_rate)

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return "Mock Chat which started at {} (at speed {}).".format(
            self.start_time,
            self.speed
        )


class LiveChat(threading.Thread):
    """ A LiveChat object represents a live youtube chat, i.e. live chat attached
    to a youtube live broadcast.

    Attributes:
        has_new_messages    A threading.Condition object that notifies all the
                            waiting threads when new messages are available.
        is_over             A threading.Event object that is set when the chat
                            is over.
        index               The index of the last available chat message.

    Methods:
        start               Start refreshing the chat via the youtube service.
    """

    index = 0
    is_over = threading.Event()
    has_new_messages = threading.Condition()

    _buffer = []
    _bkp_count = 0
    _bkp_file_name_template = "chat_ressource_backup_{}-{}.bkp"
    _save_file_name_template = "chat_ressource_{}.json"
    _timestamp = timestamp()
    _bkp_dir = os.path.join(LIVECHAT_BACKUP_DIR, datetimestamp())

    def __init__(self, youtube, id, chat, refresh_rate, **kwargs):
        """ A LiveChat object object is initialized with
        1) An authenticated youtube service (youtube)
        2) The id of the live chat (id)
        3) A Chat object in which the chat messages are put (chat)
        4) A refresh rate (refresh_rate)

        The optionnal parameter buffer_size (default 50) controls the size of
        the internal buffer size.
        """

        threading.Thread.__init__(self, name="Live chat.")
        self.chat = chat
        self.youtube = youtube
        self.id = id
        self.refresh_rate = refresh_rate

        try:
            os.mkdir(self._bkp_dir)
        except FileExistsError as e:
            pass
        else:
            print(">>> Directory {} created.".format(self._bkp_dir))
        self.buffer_size = kwargs.get("buffer_size", 50)

    def dump_buffer_to_json(self):
        """ Every LiveChat object holds a buffer with all liveChatMessage
        responses it recieved from youtube. This function dumps the buffer to a
        json file (automatically named). After the live chat is over, those
        backup files can be combined into a single chat ressource by calling
        the save_to_json method.
        """

        file_name = self._bkp_file_name_template.format(
            self._timestamp,
            self._bkp_count
        )
        file_name = os.path.join(self._bkp_dir, file_name)

        try:
            with open(file_name, 'w') as f:
                json.dump(self._buffer, f)
        except Exception as e:
            print(">>> There was a problem with backing-up the live chat.")
            print(e)
        else:
            self._buffer = []
            self._bkp_count += 1

    def save_to_json(self, base_dir, file_name=None):
        """ Save to file named 'chat_ressource_hhmmss.json' in base_dir. This
        method collects all backups made during the live chat into a single file.

        It is always a good idea to test this function BEFORE running the actual
        chat session to make sure that the data will be saved after the session.
        For example, one could do
        LiveChat().save_to_json(CURRENT_SAVE_DIR, file_name="test_save.txt")

        If, for some reason, the program crashed and the LiveChat doesn't exist
        anymore, the backups can be "manually" combined using the
        combine_live_chat_backups_to_json function in this module.
        """

        # Collecting the backups into a single list called json_object
        json_object = []
        for n in range(self._bkp_count):
            bkp_file_name = os.path.join(
                self._bkp_dir,
                self._bkp_file_name_template.format(self._timestamp, n)
            )
            try:
                with open(bkp_file_name, 'r') as f:
                    json_object.extend(json.load(f))
            except Exception as e:
                print(">>> There was a problem with loading the file {}.".format(file))
                print(e)

        # Preparing the file_name
        if file_name is None:
            file_name = self._save_file_name_template.format(timestamp())
        file_name = os.path.join(base_dir, file_name)

        # Dump json_object
        try:
            with open(file_name, 'w') as f:
                json.dump(json_object, f, indent=4)
        except Exception as e:
            print(">>> There was a problem with saving the live chat object.")


    def run(self):
        """ As the time passes, more messages are available on youtube.
        The run method makes those messages available (by retrieving them and
        then by putting them in self.chat) and notifies all waiting threads via
        its has_new_messages condition.
        """

        live_chat_messages = self.youtube.liveChatMessages()
        request = live_chat_messages.list(
            liveChatId=self.id,
            part="snippet"
        )

        while request is not None and not self.is_over.is_set():
            try:
                response = request.execute()
            except HttpError as e:
                # e.content is of type byte
                # e.content.decode() is a string representing a dict
                # Use json.loads to make the string into a dict
                e_info = json.loads(e.content.decode())
                e_message = e_info['error']['message']

                # if e_message == 'The live chat is no longer live.':
                print(">>> An HTTP error {} occurred while refreshing the chat:\n{}"
                    .format(e.resp.status, e_message)
                )
                print(">>> Closing the live chat.")
                break
            else:
                if len(response["items"]) > 0:
                    message_ressource = [item["snippet"] for item in response["items"]]

                    self.chat.extend_messages(
                        [ChatMessage(**message) for message in message_ressource]
                    )

                    self.index += len(message_ressource)

                    self._buffer.extend(message_ressource)
                    if len(self._buffer) >= self.buffer_size:
                        self.dump_buffer_to_json()

                    with self.has_new_messages:
                        self.has_new_messages.notify_all()

                request = live_chat_messages.list_next(request, response)
                time.sleep(self.refresh_rate)
        self.dump_buffer_to_json()
        self.is_over.set()
        print(">>> The live chat is over.")

    def __repr__(self):
        return "Live Chat with id {}.".format(self.id)


def mock_chat_from_file(file, chat, refresh_rate, **kwargs):
    """ Build a MockChat from a file. Here file contains a json-loadable list
    of chat messages (comming from youtube responses or ChatMessage.as_dict().
    This is the format returned by either LiveChat().save_to_json or
    Chat().save_to_json.
    """

    with open(file, 'r') as f:
        raw_messages = json.load(f)

    if "amount" in kwargs:
        raw_messages = raw_messages[:kwargs["amount"]]

    messages = [ChatMessage(**dict) for dict in raw_messages]

    return MockChat(
        messages,
        chat,
        refresh_rate,
        kwargs.get("speed", 1)
    )

def combine_live_chat_backups_to_json(files, base_dir, file_name=None):
    """ Combine the files in the list files into a single file named
    'chat_ressource_hhmmss.json' in base_dir. This function
    """

    # Collecting the backups into a single list called json_object
    json_object = []
    for file in files:
        try:
            with open(file, 'r') as f:
                json_object.extend(json.load(f))
        except Exception as e:
            print(">>> There was a problem with loading the file {}.".format(file))
            print(e)

    # Preparing the file_name
        if file_name is None:
            file_name = "chat_ressource_{}.json".format(timestamp())
        file_name = os.path.join(base_dir, file_name)

    # Dump json_object
    try:
        with open(file_name, 'w') as f:
            json.dump(json_object, f, indent=4)
    except Exception as e:
        print(">>> There was a problem with saving the chat object.")
        print(e)