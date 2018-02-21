# For the window that prompts the user with a file_name
import tkinter
from tkinter.filedialog import asksaveasfilename, askopenfilename

import os
import json

from youtube.tools import *
from youtube.chat import Chat, LiveChat

# The absolute of the directory where the script lives
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# The location of the client_secrets file
CLIENT_SECRETS_FILE = os.path.join(BASE_DIR, "client_secrets.json")

# the base name of the storage file attached to the oauth2 protocol
# STORAGE_FILE_NAME = "simardnicolas0"
# STORAGE_FILE_NAME = "andreannecharestcote"
STORAGE_FILE_NAME = "blitztutorat40"

if __name__ == "__main__":
    # # A quick dummy test to see if saving a LiveChat works
    # # It creates a dummy LiveChat and prompts the user to save it
    # tkinter.Tk().withdraw()
    # file_name = tkinter.filedialog.asksaveasfilename(title="Save LiveChat")
    # LiveChat("", "", "").save_to_json(file_name)

    # Create an authenticated youtube service
    client = get_authenticated_service(
        CLIENT_SECRETS_FILE,
        STORAGE_FILE_NAME
    )
    
    # Choose an active live broadcast
    livebroadcast = get_active_livebroadcast(client)
    if livebroadcast is None:
        exit(">>> No active live broadcasts.")
    
    # Create the Chat object where the messages will be stored
    chat = Chat()
       
    # Create the LiveChat object associated to the live broadcast
    livechat = livebroadcast.get_livechat(chat)
    print(livechat)
    
    # Start the LiveChat, i.e. start requesting messages    
    livechat.start()
    livechat.join()

    # At this points, the live chat is over...
    
    # We save the live chat
    # First, prompt the user to chose a saving file_name
    # You can replace file_name directly with a string if you want
    tkinter.Tk().withdraw()
    file_name = tkinter.filedialog.asksaveasfilename(title="Save LiveChat")
    # Then save the live chat
    livechat.save_to_json(file_name)