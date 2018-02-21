import os

from youtube.tools import *

# The absolute of the directory where the script lives
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# The location of the client_secrets file
CLIENT_SECRETS_FILE = os.path.join(BASE_DIR, "client_secrets.json")

# the base name of the storage file attached to the oauth2 protocol
# STORAGE_FILE_NAME = "simardnicolas0"
# STORAGE_FILE_NAME = "andreannecharestcote"
STORAGE_FILE_NAME = "blitztutorat40"

BLOOMBERG_CHANNEL_ID = 'UCUMZ7gohGI9HcU9VNsr2FJQ'


if __name__ == "__main__":
    client = get_authenticated_service(
        CLIENT_SECRETS_FILE,
        STORAGE_FILE_NAME
    )
    
    # Method 1
    livebroadcast = get_active_livebroadcast(client)
    print(livebroadcast.livechat_id)
    
    # # Method 2
    # livebroadcast = search_active_livebroadcast(client, BLOOMBERG_CHANNEL_ID)
    # print(livebroadcast.livechat_id)    
    