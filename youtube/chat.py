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

class ChatMessage:

    """ A ChatMessage object represents a message in a Chat.

    Attributes:
        author              Author of the message.
        published_at        Moment at which the message was published.
        content             Text content of the message.
        labels              Labels attached by classifiers.

    Representation:
    A dictionary
    {
        "author": str,
        "publishedAt": str,
        "textMessageDetails": str
        "labels": [
            str
        ]
    }
    """

    def __init__(self, author, published_at, content, labels=[]):
        self.author = author
        self.published_at = published_at # A string like '2018-01-16T16:31:12.000Z'
        self.content = content
        self.labels=labels
        
    def __repr__(self):
        return dict([
            ("author", self.author),
            ("publishedAt", self.published_at),
            ("textMessageDetails", self.content),
            ("labels", self.labels)
        ])

    def __str__(self):
        # Try to know when the message was published
        try:
            published_time = dateparser(self.published_at).time().replace(microsecond=0)
        except ValueError as e:
            published_time = self.published_at

        return "{} {:15s} at {}: {}".format(
            self.labels,
            self.author,
            published_time,
            self.content
        )


class Chat:
    """ Chat objects represent youtube chats.

    Attributes:
        lock                A threading.Lock object to lock the object
        has_new_messages    A threading.Condition object which is satisfied when
                            the chat has nes messages.
        is_over             A threading.Event object which is set when the chat
                            is over.

    Methods:
        append_messages     Append messages to the object's messages
        get_all_messages    Return all the chat messages in the chat

    Representation:
    {
        "messages": [
            ChatMessage
        ]
    }
    """

    def __init__(self):
        self.lock = threading.Lock()
        self.has_new_messages = threading.Condition()
        self.is_over = threading.Event()

    # Remove
    # def append_messages(self, messages):
        # """ Append messages to the Chat object's messages. """

        # with self.lock:
            # self._messages.extend(messages)

    # Remove
    # def get_all_messages(self):
        # """ Return all messages in the Chat object.

        # The response is a list of all ChatMessage objects in the Chat.
        # """

        # with self.lock:
            # return self._messages
            
    # def __repr__(self):
        # return dict(
            # ("messages", [message.__repr__() for message in self._messages])
        # )

    # def __str__(self):
        # return "Abstract chat class."


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
        estimated_duration


    Representation:
    {
        "messages": [
            ChatMessage
        ]
    }
    """

    index = 0
    
    def __init__(self, messages, arch_mess, refresh_rate, speed=1):
        """ A mock chat is an object constructed from a list of ChatMessage
        whose purpose is to re-create the chat thread.

        The constructor takes a list of ChatMessage objects and a refresh rate.
        The refresh rate is the frequency at which the chat checks if new
        messages are available. If speed is an integer different from one, play
        the chat at speed times the speed.
        """

        Chat.__init__(self)
        threading.Thread.__init__(self, name="Mock chat.")
        self.messages = messages
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

        with self.lock:
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
                self.messages.extend(self._arch_mess[old_index: self.index])
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


def mock_chat_from_archive(messages, arch_mess, refresh_rate, speed):
    return MockChat(
        messages,
        [chat_message_from_dict(mess) for mess in arch_mess],
        refresh_rate,
        speed
    )

def chat_message_from_dict(dic):
    """ Return a ChatMessage, given a representation of a ChatMessage. """

    return ChatMessage(
        dic.get("author", "???"),
        dic.get("publishedAt", "???"),
        dic.get("textMessageDetails", "???"),
        dic.get("labels","")
    )