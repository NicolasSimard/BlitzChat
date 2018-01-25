import youtube.tools as yt
import youtube.livebroadcast as lb
from youtube.chat import LiveChat, Chat
import youtube.layers as layers
import json
import os
import datetime

# The absolute of the directory where the script lives
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# The location of the client_secrets file
CLIENT_SECRETS_FILE = os.path.join(BASE_DIR, "client_secrets.json")

# the base name of the storage file attached to the oauth2 protocol
STORAGE_FILE_NAME = "test"

TODAY = datetime.date.today()

# The directory where the chats are archived
ARCHIVE_DIR = os.path.join(BASE_DIR, "drive-archive")

# The directory where today's chat (live or mock) will be saved
CURRENT_SAVE_DIR = os.path.join(ARCHIVE_DIR, "{}".format(TODAY))

REFRESH_RATE = 5

if __name__ == "__main__":
    # Initializing the session
    try:
        os.mkdir(CURRENT_SAVE_DIR)
    except FileExistsError as e:
        pass
    else:
        print(">>> Directory {} created.".format(CURRENT_SAVE_DIR))

    # Just making sure that the saving method works
    Chat().save_to_json(CURRENT_SAVE_DIR, file_name="test_save_delete_me.txt")

    youtube = yt.get_authenticated_service(
        CLIENT_SECRETS_FILE,
        STORAGE_FILE_NAME
    )

    live_broadcast = lb.choose_active_live_broadcast(youtube)
    if live_broadcast is None:
        exit("No active live broadcasts. ")
    # print("live broadcast: {}".format(json.dumps(live_broadcast.__repr__(), indent=4)))
    # live_broadcast.refresh()

    chat = Chat()
    # Just making sure that the saving method works
    chat.save_to_json(
        CURRENT_SAVE_DIR,
        file_name="test_save_delete_me.txt"
    )
    
    live_chat = LiveChat(
        youtube,
        live_broadcast.get_live_chat_id(),
        chat,
        REFRESH_RATE
    )
    # Just making sure that the saving method works
    live_chat.save_to_json(
        CURRENT_SAVE_DIR,
        file_name="test_save_delete_me_too.txt"
    )
    
    question_label = layers.Question(chat, live_chat)
    
    printer = layers.Printer(chat, question_label)

    print(live_chat)

    live_chat.start()
    question_label.start()
    printer.start()

    live_chat.join()
    question_label.join()
    printer.join()

    chat.save_to_json(CURRENT_SAVE_DIR)
    live_chat.save_to_json(CURRENT_SAVE_DIR)
    print("Done")

