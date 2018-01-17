from apiclient.errors import HttpError

#TODO: When refreshing a live broadcast after is has ended, there is no more
#      liveChatId is snippets and this causes an error...

class LiveBroadcast:
    """ A LiveChat object represents a Youtube live breadcast.

    Attributes:
        youtube_service     An authenticated youtube service.
        id                  The live boradcast's id.
        title               The title of the live broadcast.

    Methods:
        get_live_chat_id    Get the ID of the attached live chat.
    """

    def __init__(self, youtube_service, id, **snippet):
        """ Initialize the live broadcast from a youtube service, an id and
        keywords arguments snippet containing the snippet info of the ress. """

        self._snippet = snippet # Can change wheh the LiveBroadcast is refreshed
        self.id = id
        self.youtube_service = youtube_service

    @property
    def name(self):
        """ Return the name of the live broadcast. """
        
        return self.title
        
    @property
    def title(self):
        """ Return the title of the live broadcast. """
        
        return self._snippet.get("title", "")
        
    @property
    def published_at(self):
        """ Return the moment at which the live broadcast started. """
        
        return self._snippet.get("publishedAt", "")

    def get_live_chat_id(self):
        """ Return the id of the associated live chat. """
        
        return self._snippet.get("liveChatId", "")
      
    def refresh(self):
        try:
            response = self.youtube_service.liveBroadcasts().list(
                id=self.id,
                part="snippet"
            ).execute()
        except HttpError as e:
            print("An HTTP error {} occurred while refreshing Broadcast {}:\n{}"
                .format(e.resp.status, self.name, e.content)
            )
        self._snippet = response["items"][0]["snippet"]    
      
    def __repr__(self):
        return dict([
            ("id", self.id),
            ("snippet", self._snippet)
        ])
        
    def __str__(self):
        return "Live broadcast {}.".format(self.title)


def list_active_live_broadcasts(youtube_service):
    """List all active live broadcasts atached to the authenticated service."""

    try:
        response = youtube_service.liveBroadcasts().list(
            broadcastStatus="active",
            part="id, snippet"
        ).execute()
    except HttpError as e:
        print("An HTTP error {} occurred while retrieving live broadcasts:\n{}"
            .format(e.resp.status, e.content)
        )
    return response["items"]
    
def list_live_broadcast_by_id(youtube_service, id):
    """List all active live broadcasts attached to the authenticated service."""

    try:
        response = youtube_service.liveBroadcasts().list(
            id=id,
            part="id, snippet"
        ).execute()
    except HttpError as e:
        print("An HTTP error {} occurred while retrieving live broadcasts:\n{}"
            .format(e.resp.status, e.content)
        )
    return response["items"]

def live_broadcast_from_ress(youtube_service, ress):
    """ Return a LiveBroadcast object from a youtube_service and a liveBroadcasts
    broadcast ressource. """

    return LiveBroadcast(youtube_service, ress["id"], **ress["snippet"])

def choose_active_live_broadcast(youtube_service):
    """ Choose an active live broadcast."""

    live_broadcasts = list_active_live_broadcasts(youtube_service)

    if len(live_broadcasts) == 0:
        return None
    elif len(live_broadcasts) == 1:
        return livebroadcast_from_ress(youtube_service, live_broadcasts[0])
    else:
        print("Please choose an active live broadcast:")
        for live_broadcast in live_broadcasts:
            print("{:2d}:  id = {}"
                .format(live_broadcasts.index(live_broadcast), live_broadcast["id"])
            )
        while True:
            try:
                index = int(input("Your choice: "))
                return livebroadcast_from_ress(youtube_service, live_broadcasts[index])
            except IndexError:
                print("Invalid index.")