"""
livechat module:

Module to download youtube live chat comments attached to a live broadcast.
"""

#TODO: Replace author chanel ID with author name
#TODO: Load only new comments in refresh method
#TODO: make LiveBroadcast class

import httplib2
import os
import sys

from apiclient.discovery import build
from oauth2client.client import flow_from_clientsecrets
from apiclient.errors import HttpError
from oauth2client.file import Storage
from oauth2client.tools import argparser, run_flow
import json
from threading import Thread
import time


def get_authenticated_youtube_service(args, client_secrets_file, storage_path):
    """Get read only authenticated youtube service."""

    flow = flow_from_clientsecrets(client_secrets_file,
        scope="https://www.googleapis.com/auth/youtube.readonly",
        message="WARNING: Please configure OAuth 2.0.")

    storage = Storage("storage/{}-oauth2.json".format(storage_path))
    credentials = storage.get()

    if credentials is None or credentials.invalid:
        credentials = run_flow(flow, storage, args)

    return build("youtube", "v3", http=credentials.authorize(httplib2.Http()))

def get_active_live_broadcasts(youtube):
    """List all active live broadcasts atached to the authenticated service."""

    return youtube.liveBroadcasts().list(
        broadcastStatus="active",
        part="id, snippet"
    ).execute()["items"]

def choose_live_chat(youtube):
    try:
        live_broadcasts = get_active_live_broadcasts(youtube)
    except HttpError as e:
        print("An HTTP error {} occurred while retrieving live broadcasts:\n{}"
            .format(e.resp.status, e.content)
        )

    if len(live_broadcasts) == 0:
        return None
    if len(live_broadcasts) == 1:
        return LiveChat(youtube, live_broadcasts[0])
    print("Please choose an active live broadcast for which you want the live chat:")
    for live_broadcast in live_broadcasts:
        print("{no:2d}:  id = {}"
            .format(live_broadcasts.index(live_broadcast), live_broadcast["id"])
        )
    return LiveChat(youtube, live_broadcasts[int(input())])
        
    
def chat_message_from_ress(ress):
    return ChatMessage(
                ress["snippet"]["authorChannelId"],
                ress["snippet"]["publishedAt"],
                ress["snippet"]["textMessageDetails"]["messageText"]
           )

class ChatMessage:
    def __init__(self, author, publishedAt, message):
        self.author = author
        self.publishedAt = publishedAt
        self.message = message

    def is_question(self):
        pass

    def __repr__(self):
        return "{} at {}: {}".format(self.author, self.publishedAt, self.message)


class LiveChat:
    def __init__(self, youtube, live_broadcast_ress):
        self.youtube = youtube
        self.live_broadcast = live_broadcast_ress
        self.id = live_broadcast_ress["snippet"]["liveChatId"]
        self.messages = []
        self.last_request = None

    def append_messages(self, messages):
        self.messages += messages

    def __repr__(self):
        str = "Live Chat with id {} attached to Live Broadcast with id {}."\
              .format(self.id, self.live_broadcast["id"])
        str += "\n\nThe messages are:\n"
        for mess in self.messages:
            str += mess.__str__() + "\n"
        return str

class LiveChatRefresher(Thread):
    def __init__(self, live_chat, refresh_rate):
        Thread.__init__(self)
        self.name = "Thread for live chat with id {}".format(live_chat.id)
        self.live_chat = live_chat
        self.refresh_rate = refresh_rate

    def run(self):
        live_chat_messages = self.live_chat.youtube.liveChatMessages()
        request = live_chat_messages.list(
            liveChatId=self.live_chat.id,
            part="snippet"
        )

        while request is not None:
            try:
                response = request.execute()
            except HttpError as e:
                print("An HTTP error {} occurred while refreshing the comments:\n{}"
                    .format(e.resp.status, e.content)
                )
                break
            self.live_chat.append_messages(
                [chat_message_from_ress(ress) for ress in response["items"]]
            )
            request = live_chat_messages.list_next(request, response)
            print("Refreshing")
            time.sleep(self.refresh_rate)