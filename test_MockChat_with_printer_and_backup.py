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
ARCHIVE_DIR = os.path.join(BASE_DIR, "drive-archive")
CURRENT_SAVE_DIR = os.path.join(ARCHIVE_DIR, "{}".format(TODAY))

MESSAGE_SOURCE = os.path.join(ARCHIVE_DIR, "2017-12-12\\chat.json")

REFRESH_RATE = 1

if __name__ == "__main__":
    # Initializing the session
    try:
        os.mkdir(CURRENT_SAVE_DIR)
    except FileExistsError as e:
        print(">>> Directory {} already exists, skipping creation step.".format(CURRENT_SAVE_DIR))
    else:
        print(">>> Directory {} created.".format(CURRENT_SAVE_DIR))
        
    # Load the archived messages
    with open(MESSAGE_SOURCE, 'r') as f:
        arch_mess = json.load(f)

    chat = Chat()
    mock_chat = mock_chat_from_archive(
        chat,
        arch_mess[:10],
        REFRESH_RATE,
        speed=10
    )
    print(mock_chat)
    print("Should last {} seconds.".format(mock_chat.estimated_duration()))
    question_label = layers.Question(chat, mock_chat)
    printer = layers.Printer(chat, question_label)
    
    mock_chat.start()
    question_label.start()
    printer.start()
    
    mock_chat.join()
    question_label.join()
    printer.join()
    
    chat.save(CURRENT_SAVE_DIR)
    
