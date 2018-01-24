""" chat module defines all the classes and auxialry functions to work with
youtube chats.

The classes are:

    ChatMessage             Represents a chat message
    Chat                    Represents a general chat, with its messages
    LiveChat(Chat, Thread)  Represents a chat associated with a youtube service
    MockChat(Chat, Thread)  Represents a chat constructed from a file

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
    """ A Chat object represents a collention of messages which can vary in time.

    Attributes:
        lock                A threading.Lock object to lock the object

    Methods:
        append_messages     Append messages to the object's messages
        get_messages        Return chat messages
        append_messages     Append messages to chat object
        save                Save Chat object to JSON format using its representation
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
    chat from a Chat representation. It is a Chat object with extra properties
    and methods.

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

    def __init__(self, chat, arch_mess, refresh_rate, speed=1):
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
        Calling refresh makes those new messages available.

        Every Chat object has a condition object called has_new_messages that
        is set when there are new messages. The threads that want to wait for
        new messages and be notified when there are should use something like

        with chat.has_new_messages:
            chat.has_new_messages.wait()
            do_something_with_the_messages()
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


def mock_chat_from_file(file, chat, refresh_rate, **kwargs):
    """ Build a MockChat from a file. Here file contains a json-loadable list
    of chat messages (comming from youtube responses or ChatMessage.as_dict().
    """
    
    with open(file, 'r') as f:
        raw_messages = json.load(f)
        
    if "amount" in kwargs:
        raw_messages = raw_messages[:kwargs["amount"]]
    
    messages = [ChatMessage(**dict) for dict in raw_messages]
    
    return MockChat(
        chat,
        messages,
        refresh_rate,
        kwargs.get("speed", 1)
    )
    