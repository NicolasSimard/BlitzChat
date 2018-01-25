from youtube.chat import *
import youtube.layers as layers
import json
import time
import threading
import os
import datetime

TODAY = datetime.date.today()

# The absolute of the directory where the script lives
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

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
    question_label = layers.Question(chat, mock_chat)
    printer = layers.Printer(chat, question_label)
    
    print(mock_chat)
    print("Should last {} seconds.".format(mock_chat.estimated_duration()))
    
    layers_list = [
        mock_chat,
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
    chat.save_to_json(CURRENT_SAVE_DIR)

