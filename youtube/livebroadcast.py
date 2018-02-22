from apiclient.errors import HttpError
from .chat import LiveChat

class LiveBroadcast:
    """ A LiveChat object represents a Youtube live broadcast. It corresponds to a Youtube liveBroadcast ressource (see https://developers.google.com/youtube/v3/live/docs/liveBroadcasts#resource)

    Attributes:
        client: An authenticated youtube service.
        id: The live boradcast's id.
        title: The title of the live broadcast.
        published_at: Time at which the livebroadcast was published.
        livechat_id: The id if the associated live chat.

    Methods:
        get_livechat: Returns the associated LiveChat object
    """

    def __init__(self, client, ressource):
        """ Initialize the live broadcast from an authenticated youtube client and a Youtube liveBroadcast ressource.
        """

        self.client = client
        self.ressource = ressource

    @property
    def id(self):
        return self.ressource['id']

    @property
    def name(self):
        """ Return the name of the live broadcast. """

        return self.title

    @property
    def title(self):
        """ Return the title of the live broadcast. """

        return self.ressource['snippet']['title']

    @property
    def published_at(self):
        """ Return the moment at which the live broadcast started. """

        return self.ressource['snippet']['publishedAt']

    @property
    def livechat_id(self):
        return self.ressource['snippet'].get('liveChatId', None)
            

    def get_livechat(self, chat):
        """ Return the associated LiveChat object. """

        return LiveChat(self.client, self.livechat_id, chat)

    def __repr__(self):
        return self.ressource

    def __str__(self):
        return "Live broadcast {}.".format(self.title)