from oauth2client.tools import argparser
from apiclient.errors import HttpError

import json
from threading import Thread

import livechat as lc

CLIENT_SECRETS_FILE = "client_secrets.json"
STORAGE_FILE_NAME = "chatanalysis"
LIVE_CHAT_REFRESH_RATE = 10


youtube = lc.get_authenticated_youtube_service(
    argparser.parse_args(),
    CLIENT_SECRETS_FILE,
    STORAGE_FILE_NAME
)

live_chat = lc.choose_live_chat(youtube)
if live_chat is None:
    exit("No active Live Broadcast.")
print("Chosen live broadcast id: {}\nCorresponding live chat id: {}"
    .format(live_chat.live_broadcast["id"], live_chat.id)
)
   
lc_refresher = lc.LiveChatRefresher(
    live_chat,
    LIVE_CHAT_REFRESH_RATE
)
lc_refresher.start()
lc_refresher.join() # The main thread is paused until lc_refresher finishes

print(live_chat)
print("Exiting main thread")
