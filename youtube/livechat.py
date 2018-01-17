"""
livechat module:

Module to work with youtube live chat comments attached to a live broadcast.
"""

#TODO: Replace author chanel ID with author name
#TODO: The published_at attribute of ChatMessage should be a datetime object
#TODO: take an argument in LiveChatRefresher class to print the messages as they
#      are retrieved.
#TODO: Make sure we don't save over an existing file...

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
import dateutil.parser
import json

class ChatMessage:
    """ A ChatMessage object represents a message in a Chat.

    Attributes:
        author              Author of the message.
        published_at        Moment at which the message was published.
        content             Text content of the message.

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
        return "{} at {}: {}".format(
            self.author,
            self.published_at,
            self.content
        )


class Chat:
    """ Chat objects represent youtube chats.

    Attributes:
        messages            List of ChatMessage objects.
        lock                A threading.Lock object to lock the YoutubeChat.
        has_new_messages    A threading.Event object that is set when there are
                            new messages.
        is_over             A threading.Event object that is set when the chat
                            is over.

    Methods:
        append_messages     Append messages to the object's messages
    """

    def __init__(self):
        self.messages = []
        self.lock = threading.Lock()
        self.has_new_messages = threading.Event()
        self.is_over = threading.Event()

    def append_messages(self, messages):
        """ Append messages to the YoutubeChat object's messages. """

        self.messages += messages

    def get_messages(self):
        """ Return all messages in the Chat object. 
        
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
            ("items", self.messages)
        ])
        
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
        
        return dict([
            ("index", len(self.messages)),
            ("items", self.messages[index:])
        ])

class LiveChat(Chat):
    """ A LiveChat object represents a Youtube live chat. It is a Chat object
    with extra properties and methods.

    Attributes:
        live_broadcast      The LiveBroadcast object to which the chat is attached.
        youtube_service     The youtube service of the associated live broadcast.
        id                  The id of the live chat.
    """

    def __init__(self, live_broadcast):
        """ Initialise the LiveChat object with an authenticated youtube
        service and the corresponding live broadcast ressource.
        """

        super().__init__()
        self.live_broadcast = live_broadcast

    @property
    def youtube_service(self):
        return self.live_broadcast.youtube_service
        
    @property
    def id(self):
        return self.live_broadcast.get_live_chat_id()

    def save_to_file(self, file_path):
        """ Save a LiveChat to the file given by file_path.
        
        This prints self.__repr__() to a file.
        """
        
        with open(file_path, 'w') as file:
            json.dump(self.__repr__(), file)
        
    def __repr__(self):
        return dict([
            ("liveBroadcast", self.live_broadcast.__repr__()),
            ("liveChatId", self.id),
            ("publishedAt", self.live_broadcast.published_at.__repr__()),
            ("messages", [mess.__repr__() for mess in self.messages])
        ])

    def __str__(self):
        str = "Live Chat with id {} attached to Live Broadcast with id {}."\
              .format(self.id, self.live_broadcast.id)
        str += "\n\nThe messages are:\n"
        for message in self.messages:
            str += message.__str__() + "\n"
        return str

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
        
        
def chatmessage_from_ress(ress):
    return ChatMessage(
                ress["snippet"]["authorChannelId"],
                ress["snippet"]["publishedAt"],
                ress["snippet"]["textMessageDetails"]["messageText"]
           )

def livechat_from_livebroascast(live_broadcast):
    return LiveChat(live_broadcast)