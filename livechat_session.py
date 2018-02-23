# For the window that prompts the user with a file_name
import tkinter
from tkinter.filedialog import asksaveasfilename

import os
import json
from configparser import ConfigParser

from youtube.tools import *
from youtube.chat import Chat, LiveChat
from youtube.target import Printer, MessageFilter
from youtube.filter import get_username, convert_to_local_time

# Read the config file
config = ConfigParser()
config.read('config.ini')

CREDENTIALS = "blitztutorat40"

if __name__ == "__main__":
    # Create an authenticated youtube service
    client = get_authenticated_service(
        config['auth']['secrets'],
        CREDENTIALS
    )

    # Choose an active live broadcast
    # Method 1:
    # print(">>> Looking for active live broadcasts of authenticated client.")
    # livebroadcast = get_active_livebroadcast(client)

    # Method 2:
    # print(">>> Looking for a live broadcasts by id.")
    # livebroadcast = livebroadcast_from_id(client, '87vXWgjKFWE')

    # method 3:
    print(">>> Looking for active live broadcasts on the Blitz Channel.")
    livebroadcast = search_active_livebroadcast(client, config['blitz40']['channelid'])
    if livebroadcast is None:
        exit(">>> No active live broadcasts.")
    print(livebroadcast)

    if livebroadcast.livechat_id is None:
        exit(">>> The livechat attached to this livebroadcast is no longer active.")

    # Create the Chat object where the messages will be stored
    chat = Chat()
    chat.add_filter(get_username(client))
    chat.add_filter(convert_to_local_time)
       
    # Create the LiveChat object associated to the live broadcast
    livechat = LiveChat(client, livebroadcast.livechat_id, chat)
    print(livechat)

    # Start the LiveChat, i.e. start requesting messages    
    livechat.start()
    livechat.join()

    # At this points, the live chat is over...
    tkinter.Tk().withdraw()
    file_name = tkinter.filedialog.asksaveasfilename((
        title='Save LiveChat',
        defaultextension='json',
        initialdir=config['DEFAULT']['archive'],
        initialfile=livebroadcast.title + '.json'
    )
    # Then save the live chat
    livechat.save_to_json(file_name)