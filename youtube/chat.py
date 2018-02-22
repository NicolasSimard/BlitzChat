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
LIVECHAT_BUFFER_SIZE = 50

def timestamp():
    """" Return a string of the form hhmmss representing the time now. """
    
    now = datetime.datetime.now().time().replace(microsecond = 0).__str__()
    now = now.replace(":","") # : is not allowed in windows file names.
    return now

def datetimestamp():
    """" Return a string of the form yyyy-mm-dd_hhmmss representing the date
    and time now. """

    now = datetime.datetime.now().replace(microsecond = 0).__str__()
    now = now.replace(":","").replace(" ","_") # : is not allowed in windows file names.
    return now

class ChatMessage:
    """ A ChatMessage object represents a message in a Chat

    Attributes:
        author              Author of the message.
        published_at        Moment at which the message was published.
        content             Text content of the message.
        labels              A list of labels (strings) attached by classifiers.
    
    Methods:
        add_label           Add a label (a string) to the message
        as_dict             Return a dictionary representing the message        
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

        return {
            'author': self.author,
            'published_at': self.published_at,
            'content': self.content,
            'labels': self.labels
        }

    def __repr__(self):
        """ Returns self.as_dict().__str__(). """
        
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
        """ Append ChatMessage object to the list of messages in the chat. """
        
        if isinstance(message, ChatMessage):
            self._messages.append(message) # append is thread-safe
        else:
            print(">>> Unable to append {} to Chat object.".format(message))

    def get_messages(self, begin, end):
        """ Returns the messages between begin and end, as in
        messages[begin: end].
        """
    
        return self._messages[begin: end]

    def extend_messages(self, messages):
        """ Extend the messages with a list of ChatMessage objects.  """
        
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
            file_name = "chat_session_{}.json".format(timestamp())
        file_name = os.path.join(base_dir, file_name)

        json_object = [message.as_dict() for message in self._messages]

        if len(json_object) == 0:
            print(">>> Chat had nothing to save.")
        else:
            try:
                with open(file_name, 'w') as f:
                    json.dump(json_object, f, indent=4)
            except Exception as e:
                print(">>> There was a problem with saving the chat object.")
                print(e)
            else:
                print(">>> Chat succesfully saved.")

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
        is_over: A threading.Event object that is set when the chat is over.
        chat: The Chat object where the chat messages are put.
        start_time: The time at which the chat started. This is the moment where the first message of the chat was posted.

    Methods:
        start: Start putting the chat messages in the Chat object.
        estimated_duration: Estimated duration of the mock chat.    
    """

    index = 0
    is_over = threading.Event()

    def __init__(self, archive_file, chat, refresh_rate=5, speed=1):
        """ A mock chat is an object constructed from a list of ChatMessage
        whose purpose is to re-create the chat thread.

        The constructor takes a list of ChatMessage objects and a refresh rate.
        The refresh rate is the frequency at which the chat checks if new
        chat messages are available. If speed is an integer different from one, play
        the chat at speed times the speed.
        """

        threading.Thread.__init__(self, name="Mock chat.")
        self.chat = chat
        with open(archive_file, 'r') as f:
            self._arch_mess = json.load(f) # List of liveChatMessage ressources

        # Now self._arch_mess is a list of ChatMessage objects
        self._arch_mess = [ChatMessage(**ress) for ress in self._arch_mess]
            
        try:
            self.start_time = dateparser(self._arch_mess[0].published_at)
        except IndexError:
            print(">>> No messages in MockChat.")
        if isinstance(speed, int):
            self.speed = speed
        else:
            self.speed = 1
        self.refresh_rate = refresh_rate
        self.nbr_messages = len(self._arch_mess)

    @property
    def duration(self):
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

            time.sleep(self.refresh_rate)

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return "Mock Chat which started at {} (at speed {}).".format(
            self.start_time,
            self.speed
        )


class LiveChat(threading.Thread):
    """ A LiveChat object represents a live youtube chat, i.e. live chat attached to a youtube live broadcast.

    Attributes:
        is_over: A threading.Event object that is set when the chat is over.
        chat: The Chat object where the chat messages are put.
        id: id of the livechat

    Methods:
        start: Start refreshing the chat via the youtube service.
        dump_buffer_to_json: Dump the buffer in json format
        save_to_json: Save the LiveChat object.
    """

    is_over = threading.Event()

    _buffer = []
    _bkp_file_paths = []
    _bkp_file_name_template = "chat_ressource_backup_{}.bkp"
    _default_save_file_name_template = "chat_ressource_{}.json"
    _bkp_dir = os.path.join(LIVECHAT_BACKUP_DIR, datetimestamp())

    def __init__(self, client, id, chat, refresh_rate=5, **kwargs):
        """ Initialize a LiveChat object.
        
        Arguments:
            client: An authenticated youtube service.
            id: the id of the live chat.
            chat: Chat object in which the chat messages are put.
            refresh_rate: The refresh rate (default=5)
        """

        threading.Thread.__init__(self, name="Live chat.")
        self.chat = chat
        self.client = client
        self.id = id
        self.refresh_rate = refresh_rate

        try:
            os.mkdir(self._bkp_dir)
        except FileExistsError as e:
            pass
        else:
            print(">>> Directory {} created.".format(self._bkp_dir))

    def dump_buffer_to_json(self):
        """ Every LiveChat object holds a buffer with all liveChatMessage
        responses it recieved from youtube. This function dumps the buffer to a
        json file (automatically named). After the live chat is over, those
        backup files can be combined into a single chat ressource by calling
        the save_to_json method.
        """

        file_name = self._bkp_file_name_template.format(timestamp())
        file_name = os.path.join(self._bkp_dir, file_name)

        try:
            with open(file_name, 'w') as f:
                json.dump(self._buffer, f)
        except Exception as e:
            print(">>> There was a problem with backing-up the live chat.")
            print(e)
        else:
            self._buffer = []
            self._bkp_file_paths.append(file_name)

    def save_to_json(self, file_name):
        """ Save to file_name. This method collects all backups made during the live chat into a single file.

        It is always a good idea to test this function BEFORE running the actual chat session to make sure that the data will be saved after the session.
        For example, one could do
        LiveChat().save_to_json(file_name="test_save.txt")

        If, for some reason, the program crashed and the LiveChat doesn't exist
        anymore, the backups can be "manually" combined using the
        combine_live_chat_backups_to_json function in this module.
        """

        # Collecting the backups into a single list called json_object
        json_object = []
        for file in self._bkp_file_paths:
            try:
                with open(file, 'r') as f:
                    json_object.extend(json.load(f))
            except Exception as e:
                print(">>> There was a problem with loading the file {}.".format(file))
                print(e)

        if len(json_object) == 0:
            print(">>> Live chat is empty, but let's save anyway!")
        # Dump json_object
        try:
            with open(file_name, 'w') as f:
                json.dump(json_object, f, indent=4)
        except Exception as e:
            print(">>> There was a problem with saving the live chat object.")
        else:
            print(">>> Live chat succesfully saved to {}.".format(file_name))

    def run(self):
        """ As the time passes, more messages are available on youtube.
        The run method makes those messages available (by retrieving them and
        then by putting them in self.chat) and notifies all waiting threads via
        its has_new_messages condition.
        """

        live_chat_messages = self.client.liveChatMessages()
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
                self.is_over.set()
            else:
                if len(response["items"]) > 0:
                    message_ressource = [item["snippet"] for item in response["items"]]

                    # Put messages in the chat
                    self.chat.extend_messages(
                        [ChatMessage(**message) for message in message_ressource]
                    )

                    self._buffer.extend(message_ressource)
                    if len(self._buffer) >= LIVECHAT_BUFFER_SIZE:
                        self.dump_buffer_to_json()

                request = live_chat_messages.list_next(request, response)
                time.sleep(self.refresh_rate)
        self.dump_buffer_to_json()
        print(">>> The live chat is over.")

    def __repr__(self):
        return "Live Chat with id {}.".format(self.id)


# REMOVE: build a MockChat right from ressource...
def mock_chat_from_file(file, chat, refresh_rate, **kwargs):
    """ Build a MockChat from a file. Here file contains a json-loadable list
    of chat messages (comming from a file returned by Chat().save_to_json or
    LiveChat().save_to_json).
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

def combine_liveChatMessage_ressources(files):
    """ Combine the lists of youtube liveChatMessage ressources in the files 
    into a single list and return the list.
    """

    # Collecting the backups into a single list called json_object
    messages = []
    for file in files:
        try:
            with open(file, 'r') as f:
                new_messages = json.load(f)
        except Exception as e:
            print(">>> There was a problem with loading the file {}.".format(file))
            print(e)
        else:
            # Keep only the messages not already in messages
            new_messages = [mess for mess in new_messages if mess not in messages]
            messages.extend(new_messages)
    
    # Sort according to time
    messages = sorted(messages, key=(lambda mess: dateparser(mess.get("publishedAt"))))
    
    return messages
        
def combine_live_chat_backups_in_dir(dir, file_name):
    """ Combines all the live chat backups in the directory dir and saves it
    in file_name (as a json object).
    """
    
    files = [os.path.join(dir, file) for file in os.listdir(dir)]
    json_object = combine_liveChatMessage_ressources(files)
    
    # Dump json_object
    try:
        with open(file_name, 'w') as f:
            json.dump(json_object, f, indent=4)
    except Exception as e:
        print(">>> There was a problem with saving the chat object.")
        print(e)
    print(">>> Succesfully saved to ressource to {}.".format(file_name))
 
       