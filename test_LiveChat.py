from youtube import tools, chat, livebroadcast, layers
#from youtube.chat import LiveChat, Chat, LIVECHAT_BACKUP_DIR
#import youtube.layers as layers
import json
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

REFRESH_RATE = 5

if __name__ == "__main__":
    # Initializing the session
    try:
        os.mkdir(CURRENT_SAVE_DIR)
    except FileExistsError as e:
        pass
    else:
        print(">>> Directory {} created.".format(CURRENT_SAVE_DIR))# Initializing the session    
    
    try:
        os.mkdir(chat.LIVECHAT_BACKUP_DIR)
    except FileExistsError as e:
        pass
    else:
        print(">>> Directory {} created.".format(chat.LIVECHAT_BACKUP_DIR))


    youtube = tools.get_authenticated_service(
        CLIENT_SECRETS_FILE,
        STORAGE_FILE_NAME
    )

    # live_broadcast = livebroadcast.choose_active_live_broadcast(youtube)
    # if live_broadcast is None:
        # exit("No active live broadcasts. ")
    # print("live broadcast: {}".format(json.dumps(live_broadcast.__repr__(), indent=4)))
    # live_broadcast.refresh()

    chat_messages = chat.Chat()

    live_chat = chat.LiveChat(
        youtube,
        "", #live_broadcast.get_live_chat_id(),
        chat_messages,
        REFRESH_RATE,
        buffer_size=5 # For testing
    )

    question_label = layers.Question(chat_messages, live_chat)

    printer = layers.Printer(chat_messages, question_label)

    layers_list = [
        live_chat,
        question_label,
        printer
    ]

    # Start the threads
    for layer in layers_list:
        layer.start()
        
    print(live_chat)
    
    # Wait for all threads to be over
    for layer in layers_list:
        layer.join()
    
    # Save the current session
    chat_messages.save_to_json(CURRENT_SAVE_DIR)
    live_chat.save_to_json(CURRENT_SAVE_DIR)

