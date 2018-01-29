from youtube.chat import *
import youtube.layers as layers
from youtube import tools
import json
import time
import threading
import os
import datetime

# The absolute of the directory where the script lives
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

TODAY = datetime.date.today()

# The location of the client_secrets file
CLIENT_SECRETS_FILE = os.path.join(BASE_DIR, "client_secrets.json")

# the base name of the storage file attached to the oauth2 protocol
STORAGE_FILE_NAME = "test"

# The directory where the chats are archived
ARCHIVE_DIR = os.path.join(BASE_DIR, "drive-archive")

# The directory where today's chat (live or mock) will be saved
CURRENT_SAVE_DIR = os.path.join(ARCHIVE_DIR, "{}".format(TODAY))

# The source of the messages for the mock chat
MESSAGE_SOURCE = os.path.join(ARCHIVE_DIR, "2017-12-12\\chat_session_0.json")
REFRESH_RATE = 1

if __name__ == "__main__":
    # Initializing the session
    try:
        os.mkdir(CURRENT_SAVE_DIR)
    except FileExistsError as e:
        pass
    else:
        print(">>> Directory {} created.".format(CURRENT_SAVE_DIR))
        
    chat = Chat()
    mock_chat = mock_chat_from_file(
        MESSAGE_SOURCE,
        chat,
        REFRESH_RATE,
        speed=50
    )
    channel_title = layers.ChannelTitle(
        chat,
        mock_chat,
        tools.get_authenticated_service(
            CLIENT_SECRETS_FILE,
            STORAGE_FILE_NAME
        )
    )
    question_label = layers.Question(chat, channel_title)
    printer = layers.Printer(chat, question_label)
    
    print(mock_chat)
    print("Should last {} seconds.".format(mock_chat.estimated_duration()))
    
    layers_list = [
        mock_chat,
        channel_title,
        question_label,
        printer
    ]

    # Start the threads
    for layer in layers_list:
        layer.start()
    
    # Wait for all threads to be over
    for layer in layers_list:
        layer.join()
    
    # Save the current session
    # chat.save_to_json(CURRENT_SAVE_DIR)

