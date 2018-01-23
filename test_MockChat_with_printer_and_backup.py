import youtube.chat as chat
import youtube.layers as layers
import json
import time
import threading
import os

# The absolute of the directory where the script lives
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ARCHIVE_DIR = os.path.join(BASE_DIR, "drive-archive")

MESSAGE_SOURCE = os.path.join(ARCHIVE_DIR, "2017-12-12\\chat.json")

BKP_DIR = os.path.join(ARCHIVE_DIR, "2018-01-22")
SAVE_DIR = os.path.join(ARCHIVE_DIR, "2018-01-22")

REFRESH_RATE = 1

if __name__ == "__main__":
    with open(MESSAGE_SOURCE, 'r') as f:
        arch_mess = json.load(f)

    messages = []
    
    layers_list = []
    
    mock_chat = chat.mock_chat_from_archive(
        messages,
        arch_mess[:10],
        REFRESH_RATE,
        speed=5
    )
    
    question_label = layers.Question(messages, mock_chat)
    
    printer = layers.Printer(messages, question_label)
    
    saver = layers.LiveBackUp(messages, question_label, BKP_DIR)

    print(mock_chat)
    print("Should last {} seconds.".format(mock_chat.estimated_duration()))
    
    mock_chat.start()
    question_label.start()
    printer.start()
    saver.start()
    
