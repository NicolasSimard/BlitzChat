import httplib2
import json

from apiclient.discovery import build
from oauth2client.client import flow_from_clientsecrets
from apiclient.errors import HttpError
from oauth2client.file import Storage
from oauth2client.tools import argparser, run_flow

from .livebroadcast import LiveBroadcast

def list_of_choices(L):
    if len(L) == 1:
        return 0
    else:
        print("Please choose an element:")
        for elem in L:
            print("{:2d}: {}".format(elem))
        while True:
            try:
                index = int(input("Your choice: "))
                return index
            except IndexError:
                print("Invalid index.")

# Use ..\\config.ini to see where the storage is and replace storage by identity.
def get_authenticated_service(client_secrets_file, storage_path, args = None):
    """Get read only authenticated youtube service."""

    if args is None: args = argparser.parse_args()

    flow = flow_from_clientsecrets(client_secrets_file,
        scope="https://www.googleapis.com/auth/youtube.readonly",
        message="WARNING: Please configure OAuth 2.0.")

    storage = Storage("storage/{}-oauth2.json".format(storage_path))
    credentials = storage.get()

    if credentials is None or credentials.invalid:
        credentials = run_flow(flow, storage, args)

    return build("youtube", "v3", http=credentials.authorize(httplib2.Http()))

def livebroadcast_from_id(client, id):
    """ Given an authenticated client and a live broadcast id, request the
    corresponding liveBroadcast ressource. If successful, returns the
    corresponding LiveBroadcast object. Otherwise, returns None.
    """

    request = client.liveBroadcasts().list(
        id=id,
        part="id, snippet"
    )
    try:
        response = request.execute()
    except HttpError as e:
        print("An HTTP error {} occurred while retrieving live broadcasts:\n{}"
            .format(e.resp.status, e.content)
        )

    if len(response['items']) == 1:
        return LiveBroadcast(response['items'][0])
    else:
        return None

def search_active_livebroadcast(client, id):
    """ Given an authenticated client and a channel id, search for all active live broadcasts and request the corresponding ressources. If the request was successful and there is more than one ressource, let the user choose the live broadcast. Returns the id of the chosen live broadcast or None if no live boradcasts were found.
    """

    # Try to find the active live broadcast id
    request = client.search().list(
        part='snippet',
        maxResults=25,
        channelId=id,
        type='video',
        eventType='live'
    )
    try:
        response = request.execute()
    except HttpError as e:
        print("An HTTP error {} occurred while retrieving live broadcasts:\n{}"
            .format(e.resp.status, e.content)
        )



    # Return None if no results were found
    if len(response['items']) == 0: return None

    choice = list_of_choices([ress['id']['videoId'] for ress in response['items']])
    id = response['items'][choice]['id']['videoId']
    print(id)
    return livebroadcast_from_id(client, id)

def get_active_livebroadcast(client):
    """ Given an authenticated client, choose one of its active live broadcasts. Returns the corresponding LiveBroadcast object or None if no live boradcasts were found.
    """

    request = client.liveBroadcasts().list(
        broadcastStatus='active',
        part='id, snippet'
    )
    try:
        response = request.execute()
    except HttpError as e:
        print("An HTTP error {} occurred while retrieving live broadcasts:\n{}"
            .format(e.resp.status, e.content)
        )

    # Return None if no results were found
    if len(response['items']) == 0: return None

    choice = list_of_choices([ress['id'] for ress in response['items']])

    return LiveBroadcast(response['items'][choice])

def get_channel_title(client, id):
    request = client.channels().list(
        id=id,
        part='snippet'
    )
    try:
        response = request.execute()
    except HttpError as e:
        print("An HTTP error {} occurred while retrieving live broadcasts:\n{}"
            .format(e.resp.status, e.content)
        )

    return response['items'][0]['snippet'].get('title', 'unknown')