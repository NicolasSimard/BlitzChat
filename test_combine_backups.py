from youtube.chat import combine_live_chat_backups_to_json
import datetime
import os

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

    combine_live_chat_backups_to_json(
        [".chat_ressource_backup_{}.bkp".format(n) for n in range(5)],
        CURRENT_SAVE_DIR
    )

