# For the window that prompts the user with a file_name
import tkinter
from tkinter.filedialog import asksaveasfilename

import os
import json
from configparser import ConfigParser

from youtube.tools import *
from youtube.chat import LiveChat
from youtube.target import Session

# Read the config file
config = ConfigParser()
config.read('config.ini')

CREDENTIALS = 'nicolas'

if __name__ == '__main__':
    # Create an authenticated youtube service
    client = get_authenticated_service(
        config['auth']['secrets'],
        CREDENTIALS
    )

    # Choose an active live broadcast
    livebroadcast = livebroadcast_from_id(client, '')
    if livebroadcast is None:
        exit(">>> No active live broadcasts.")
    print(livebroadcast)

    if livebroadcast.livechat_id is None:
        exit(">>> The livechat attached to this livebroadcast is no longer active.")

    # Create the Chat object where the messages will be stored
    session = Session()

    # Create the LiveChat object associated to the live broadcast
    livechat = LiveChat(client, livebroadcast.livechat_id, session)
    print(livechat)

    livechat.start_refresh_loop()

    # At this points, the live chat is over...
    tkinter.Tk().withdraw()
    file_name = tkinter.filedialog.asksaveasfilename(
        title='Save LiveChat',
        defaultextension='json',
        initialdir=config['DEFAULT']['archive'],
        initialfile=livebroadcast.title + '.json'
    )
    # Then save the live chat
    livechat.save_to_json(file_name)