# For the window that prompts the user with a file_name
import tkinter
from tkinter.filedialog import askopenfilename, asksaveasfilename

import os
import json
from configparser import ConfigParser

from youtube.chat import Chat, MockChat
from youtube.tools import get_authenticated_service
from youtube.filter import get_username, convert_to_local_time

# Read the config file
config = ConfigParser()
config.read('config.ini')

CREDENTIALS = "blitztutorat40"

if __name__ == "__main__":
    client = get_authenticated_service(
        config['auth']['secrets'],
        CREDENTIALS
    )

    # Built a chat object
    chat = Chat()
    chat.add_filter(get_username(client))
    chat.add_filter(convert_to_local_time)

    # Create the mockchat
    tkinter.Tk().withdraw()
    ressources = tkinter.filedialog.askopenfilename(title="Open MockChat")
    mockchat = MockChat(ressources, chat, speed=500) 
    print(mockchat)
    print("The chat should last {} seconds.".format(mockchat.duration))

    mockchat.start()
    mockchat.join()

    save_file = tkinter.filedialog.asksaveasfilename(title="Save session")
    chat.save_pretty_chat(save_file)