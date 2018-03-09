# For the window that prompts the user with a file_name
import tkinter
from tkinter.filedialog import asksaveasfilename

import os
import json
from configparser import ConfigParser
import datetime
from threading import Timer
import time

from youtube.tools import *
from youtube.chat import LiveChat
from youtube.target import Session

# Read the config file
config = ConfigParser()
config.read('config.ini')

CREDENTIALS = 'redlive'
START_TIME = datetime.datetime(2018, 3, 10, 17)
INTERVAL = 5

def archive_chat():
    client = get_authenticated_service(
        config['auth']['secrets'],
        CREDENTIALS
    )

    # Try finding an active live broadcast by channelid
    livebroadcast = search_active_livebroadcast(
        client,
        config['redlive']['channelid']
    )
    
    # Try finding an active live broadcast by client
    if livebroadcast is None:
        livebroadcast = get_active_livebroadcast(client)
    
    # In nothing worked, return
    if livebroadcast is None:
        print(">>> {}: No active live broadcast.".format(datetime.datetime.now()))
        return False
    
    print(livebroadcast)

    if livebroadcast.livechat_id is None:
        print(">>> The livechat attached to this livebroadcast is no longer active.")
        return True

    # Create the Chat object where the messages will be stored
    session = Session()

    # Create the LiveChat object associated to the live broadcast
    livechat = LiveChat(client, livebroadcast.livechat_id, session)
    print(livechat)

    # Start collecting messages until none are left...
    livechat.start_refresh_loop()

    return True
    
if __name__ == '__main__':
    print("for RedLive")
    delay = (START_TIME - datetime.datetime.now()).seconds
    print(">>> Scheduled at{}. {} seconds until program runs.".format(START_TIME, delay))
    time.sleep(delay)
    
    # Try to find the broadcast until one is found...
    while True:
        if archive_chat(): break
        time.sleep(INTERVAL)
    print(">>> Task done.")