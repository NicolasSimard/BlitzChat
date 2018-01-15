"""
livechat module:

Module to work with youtube live chat comments attached to a live broadcast.
"""

#TODO: Replace author chanel ID with author name
#TODO: The published_at attribute of ChatMessage should be a datetime object
#TODO: Load only new comments in refresh method (make a messages() and messages_next()
#      methods in Chat class. The methods responses should include a bookmark and the messages)
#TODO: take an argument in LiveChatRefresher class to print the messages as they
#      are retrieved.

from apiclient.errors import HttpError
import threading


class ChatMessage:
    """ A ChatMessage object represents a message in a Chat.

    Attributes:
        author              Author of the message.
        published_at        Moment at which the message was published.
        content             Text content of the message.

    """

    def __init__(self, author, published_at, content):
        self.author = author
        self.published_at = published_at
        self.content = content

    def __repr__(self):
        return self.__str__()

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

    def __repr__(self):
        return self.__str__()

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

        while request is not None and input("Stop?") != "Y": #VERB
            try:
                response = request.execute()
            except HttpError as e:
                print("An HTTP error {} occurred while refreshing the comments:\n{}"
                    .format(e.resp.status, e.content)
                )
                break
            with self.live_chat.lock:
                self.live_chat.append_messages(
                    [chatmessage_from_ress(ress) for ress in response["items"]]
                )
            request = live_chat_messages.list_next(request, response)
            time.sleep(self.refresh_rate)
        
        print(self.live_chat) #VERB


def chatmessage_from_ress(ress):
    return ChatMessage(
                ress["snippet"]["authorChannelId"],
                ress["snippet"]["publishedAt"],
                ress["snippet"]["textMessageDetails"]["messageText"]
           )

def livechat_from_livebroascast(live_broadcast):
    return LiveChat(live_broadcast)