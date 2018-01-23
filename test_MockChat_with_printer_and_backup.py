import youtube.tools as yt
import youtube.other as other
import youtube.chat as chat
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
        messages = json.load(f)

    mock_chat = chat.mock_chat_from_archive(messages[:50], REFRESH_RATE, speed=20)
    print(mock_chat)
    print("Should last {} seconds.".format(mock_chat.estimated_duration()))
    
    mock_chat.start()
    other.Printer(mock_chat).start()
    other.LiveBackUp(mock_chat, BKP_DIR).start()
    
