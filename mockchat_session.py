# For the window that prompts the user with a file_name
import tkinter
from tkinter.filedialog import askopenfilename, asksaveasfilename

import os
import json

from youtube.chat import Chat, MockChat
from youtube.tools import get_authenticated_service
from youtube.filter import get_username, convert_to_local_time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CLIENT_SECRETS_FILE = os.path.join(BASE_DIR, "client_secrets.json")
STORAGE_FILE_NAME = "simardnicolas0"


tkinter.Tk().withdraw()

client = get_authenticated_service(
    CLIENT_SECRETS_FILE,
    STORAGE_FILE_NAME
)

# Built a chat object
chat = Chat()
chat.add_filter(get_username(client))
chat.add_filter(convert_to_local_time)

# Create the mockchat
ressources = tkinter.filedialog.askopenfilename(title="Open MockChat")
mockchat = MockChat(ressources, chat, speed=500) 
print(mockchat)
print("The chat should last {} seconds.".format(mockchat.duration))

mockchat.start()
mockchat.join()

save_file = tkinter.filedialog.asksaveasfilename(title="Save session")
chat.save_pretty_chat(save_file)