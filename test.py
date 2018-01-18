import youtube.tools as yt
import youtube.livebroadcast as lb
import youtube.livechat as lc
import json

CLIENT_SECRETS_FILE = "client_secrets.json"
STORAGE_FILE_NAME = "test"
LIVE_CHAT_REFRESH_RATE = 5

SAVING_PATH = "archive\\test.json"

if __name__ == "__main__":
    service = yt.get_authenticated_service(CLIENT_SECRETS_FILE, STORAGE_FILE_NAME)
    
    live_broadcast = lb.choose_active_live_broadcast(service)
    if live_broadcast is None:
        exit("No active live broadcasts. ")
    print("live broadcast: {}".format(json.dumps(live_broadcast.__repr__(), indent=4)))
    live_broadcast.refresh()
    
    live_chat = lc.livechat_from_livebroascast(live_broadcast) 
    print("live chat: {}".format(json.dumps(live_chat.__repr__(), indent=4)))
    live_chat.save_to_file(SAVING_PATH)
    
    refresher = lc.LiveChatRefresher(live_chat, LIVE_CHAT_REFRESH_RATE)
    refresher.start()
    
    print("Waiting for new messages.")
    live_chat.has_new_messages.wait()
    print("New messages!")
    
    print("Waiting for the live chat to end.")
    live_chat.is_over.wait()
    print("Done waiting for the live chat to end.")
    
    live_broadcast.refresh()
    live_chat.save_to_file(SAVING_PATH)
    print("live chat: {}".format(json.dumps(live_chat.__repr__(), indent=4)))
        
    
    