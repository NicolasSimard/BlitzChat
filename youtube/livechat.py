"""
livechat module:

Module to work with youtube live chat comments attached to a live broadcast.
"""

#TODO: Replace author chanel ID with author name
#TODO: The published_at attribute of ChatMessage should be a datetime object
#TODO: take an argument in LiveChatRefresher class to print the messages as they
#      are retrieved.
#TODO: Make sure we don't save over an existing file...
#TODO: Use RLock instead of Lock...

# NOTE: To convert the string s='2018-01-16T16:31:12.000Z' to a datetime
#       object: dt = dateutil.parser.parse(s). The tzinfo will be tzutc()
#       Given such a UTC time dt, you can convert it to a local time:
#       >>> dt = dateutil.parser.parse(s); dt
#       datetime.datetime(2018, 1, 16, 16, 31, 12, tzinfo=tzutc())
#       >>> dt.astimezone(dateutil.tz.tzlocal())
#       datetime.datetime(2018, 1, 16, 11, 31, 12, tzinfo=tzlocal())

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

    Representation:
    A dictionarry
    {
        "author": str,
        "publishedAt": str,
        "textMessageDetails": str
    }
    """

    def __init__(self, author, published_at, content):
        self.author = author
        self.published_at = published_at # A string like '2018-01-16T16:31:12.000Z'
        self.content = content

    def __repr__(self):
        return dict([
            ("author", self.author),
            ("publishedAt", self.published_at),
            ("textMessageDetails", self.content)
        ])

    def __str__(self):
        return "{:20s} at {}: {}".format(
            self.author,
            re.search('\d{2}:\d{2}:\d{2}', self.published_at).group(0),
            self.content
        )


class Chat:
    """ Chat objects represent youtube chats.

    Attributes:
        messages            List of ChatMessage objects.

    Methods:
        append_messages     Append messages to the object's messages
        
    Representation:
    {
        "messages": [
            ChatMessage
        ]
    }
    """

    def __init__(self, messages):
        self.messages = messages
        self.lock = threading.Lock()
        self.has_new_messages = threading.Condition()
        self.is_over = threading.Event()

    def append_messages(self, messages):
        """ Append messages to the Chat object's messages. """

        
        # The append() method is thread safe, so we use it instead of locking
        for message in messages:
            self.messages.append(message)

    def get_all_messages(self):
        """ Return all messages in the Chat object. 
        
        The response is a list of all ChatMessage objects in the Chat.
        """
        
        return self.messages

    def __repr__(self):
        return dict(
            ("messages", [mess.__repr__() for mess in self.messages])
        )
        
    def __str__(self):
        str = "The messages are:\n"
        for message in self.messages:
            str += message.__str__() + "\n"
        return str
 

class MockChat(Chat):
    """ A MockChat object represents a mock chat, i.e. a reproduction of a live
    chat from a Chat representation. It is a Chat object with extra properties
    and methods.
    
    Attributes:
        messages            List of ChatMessage objects.
        has_new_messages    A threading.Condition object that notifies all the
                            waiting threads when new messages are available.
        is_over             A threading.Event object that is set when the chat
                            is over.
        start_time          The time at which the chat started. This is the
                            moment where the first message of the chat was posted.
    
    Methods: 
    
    Representation:
    {
        "messages": [
            ChatMessage
        ]
    }
    """
    
    def __init__(self, messages, speed=1):
        """ A mock chat is an object constructed from a list of ChatMessage
        whose purpose is to re-create the chat thread.
        
        The constructor takes a list of ChatMessage objects. If speed is an
        integer different from one, play the chat at speed times the speed.
        """
        
        super().__init__(messages)
        try:
            self.start_time = dateparser(self.messages[0].published_at)
        except IndexError:
            print("No messages in MockChat.")
        if isinstance(speed, int):
            self.speed = speed
        else:
            self.speed = 1
        self._actual_start_time = datetime.datetime.now()
        self._last_refresh_index = 0
    
    def get_messages_next(self, index):
        """ Return the messages in the Chat object starting from index. 
        
        The response is a dictionnary
        {
            "index": int,
            "items":[
                ChatMessage
            ]
        }
        
        where index is an integer containing the index of the last
        message in the list of messages that was returned. This index
        can then be used in the get_messages_next method.
        """

        # Note that the slice operator returns the empty list in L[a:b] if a>=b
        return dict([
            ("index", self._last_refresh_index),
            ("items", self.messages[index:self._last_refresh_index])
        ])
    
    def refresh(self):
        """ As the time passes, more messages are available in the MockChat.
        Calling refresh makes those new messages available.
        
        Every Chat object has a condition object called has_new_messages that
        is set when there are new messages. The threads that want to wait for
        new messages and be notified when there are should use something like
        
        with chat.has_new_messages:
            chat.has_new_messages.wait()
            do_something_with_the_messages() 
        """
        
        delta = datetime.datetime.now() - self._actual_start_time
        delta *= self.speed # Accelerate time
        new_messages = False
        while self._last_refresh_index < len(self.messages) \
            and dateparser(self.messages[self._last_refresh_index].published_at) < (self.start_time + delta):
            self._last_refresh_index += 1
            new_messages = True
        
        if new_messages:
            with self.has_new_messages:
                self.has_new_messages.notify_all()
                
        if self._last_refresh_index == len(self.messages):
            self.is_over.set()
        
    def __str__(self):
        str = "Mock Chat which started at {} (at speed {}).\n".format(
            self.start_time,
            self.speed
        )
        
        # for message in self.messages[:self._last_refresh_index]:
            # str += message.__str__() + "\n"
        return str

        
class MockChatRefresher(threading.Thread):
    def __init__(self, mock_chat, refresh_rate, name=None):
        super().__init__(name=name)
        self.mock_chat = mock_chat
        self.refresh_rate = refresh_rate

    def run(self):
        while not self.mock_chat.is_over.is_set():
            time.sleep(self.refresh_rate)
            self.mock_chat.refresh()
            
        print("MockChatRefresher {} closing".format(self.name))

 
class LiveChat(Chat):
    """ A LiveChat object represents a Youtube live chat. It is a Chat object
    with extra properties and methods.

    Attributes:
        live_broadcast      The LiveBroadcast object to which the chat is attached.
        youtube_service     The youtube service of the associated live broadcast.
        id                  The id of the live chat.
    
    Representation:
    {
        "liveBroadcast": LiveBroadcast,
        "liveChatId": str,
        "publishedAt" = str,
        "messages": [
            ChatMessage
        ]
    }
    """

    def __init__(self, live_broadcast):
        """ Initialise the LiveChat object with an authenticated youtube
        service and the corresponding live broadcast ressource.
        """

        super().__init__([])
        self.live_broadcast = live_broadcast
        self.id = self.live_broadcast.get_live_chat_id()        

    @property
    def youtube_service(self):
        return self.live_broadcast.youtube_service

    def get_messages_next(self, index):
        """ Return the messages in the LiveChat object starting from index. 
        
        The response is a dictionnary
        {
            "index": int,
            "items":[
                ChatMessage
            ]
        }
        
        where index is an integer containing the index of the last
        message in the list of messages that was returned. This index
        can then be used in the get_messages_next method.
        """
        
        return dict([
            ("index", len(self.messages)),
            ("items", self.messages[index:])
        ])
        
    def save_to_file(self, file_path):
        """ Save a LiveChat to the file given by file_path.
        
        This prints self.__repr__() to a file.
        """
        
        with open(file_path, 'w') as file:
            json.dump(self.__repr__(), file)
        
    def __repr__(self):
        live_chat_info = dict([
            ("liveBroadcast", self.live_broadcast.__repr__()),
            ("liveChatId", self.id),
            ("publishedAt", self.live_broadcast.published_at.__repr__())
        ])
        return live_chat_info.update(super().__repr__())

    def __str__(self):
        str = "Live Chat with id {} attached to Live Broadcast with id {}.\n"\
              .format(self.id, self.live_broadcast.id)
        return str + super().__str__()

        
class LiveChatRefresher(threading.Thread):
    def __init__(self, live_chat, refresh_rate):
        super().__init__()
        self.name = "Thread for id {}".format(live_chat.id)
        self.live_chat = live_chat
        self.refresh_rate = refresh_rate

    def run(self):
        live_chat_messages = self.live_chat.youtube_service.liveChatMessages()
        request = live_chat_messages.list(
            liveChatId=self.live_chat.id,
            part="snippet"
        )

        while request is not None: #and input("Stop?") != "Y": #VERB
            self.live_chat.has_new_messages.clear()
            try:
                response = request.execute()
            except HttpError as e:
                # e.content is of type byte
                # e.content.decode() is a string representing a dict
                # Use json.loads to make the string into a dict
                e_info = json.loads(e.content.decode())           
                e_message = e_info['error']['message']
                
                if e_message == 'The live chat is no longer live.':
                    print(e_message)
                    self.live_chat.is_over.set()
                else:
                    print("An HTTP error {} occurred while refreshing the chat:\n{}"
                        .format(e.resp.status, e_message)
                    )
                break
            with self.live_chat.lock:
                if len(response["items"]) > 0:
                    self.live_chat.has_new_messages.set()
                self.live_chat.append_messages(
                    [chatmessage_from_ress(ress) for ress in response["items"]]
                )
            request = live_chat_messages.list_next(request, response)
            time.sleep(self.refresh_rate)
        
        print(self.live_chat) #VERB
        

class LiveChatBkp(threading.Thread):
    """ A thread that backs up a LiveChat periodically. """
    def __init__(self, live_chat, saving_file, **kwargs):
        super().__init__()
        self.saving_file = saving_file
        
        
    def run(self):
        pass
        

class ChatPrinter(threading.Thread):
    def __init__(self, chat, name=None):
        super().__init__(name=name)
        self.chat = chat
        
    def run(self):
        bookmark = 0
        while not self.chat.is_over.is_set():
            with self.chat.has_new_messages:
                self.chat.has_new_messages.wait()
                response = self.chat.get_messages_next(bookmark)
                bookmark = response.get("index", 0)
                for message in response.get("items", []):
                    print(message.__str__())
        
        print("ChatPrinter {} closing.".format(self.name))
        
        
def chatmessage_from_ress(ress):
    """ Return a ChatMessage, given a youtube#liveChatMessage ressource. """
    return ChatMessage(
        ress["snippet"]["authorChannelId"],
        ress["snippet"]["publishedAt"],
        ress["snippet"]["textMessageDetails"]["messageText"]
    )
          
def chat_message_from_dict(dic):
    """ Return a ChatMessage, given a representation of a ChatMessage. """

    return ChatMessage(
        dic.get("author", "???"),
        dic.get("publishedAt", "???"),
        dic.get("textMessageDetails", "???")
    )
           
def chat_from_archive(message_list):
    return Chat([chat_message_from_dict(mess) for mess in message_list])
    
def mock_chat_from_archive(message_list, speed=1):
    return MockChat([chat_message_from_dict(mess) for mess in message_list], speed)
           
def livechat_from_livebroascast(live_broadcast):
    return LiveChat(live_broadcast)