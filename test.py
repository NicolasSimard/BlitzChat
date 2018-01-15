import youtube.tools as yt
import youtube.livebroadcast as lb
import youtube.livechat as lc
import json

CLIENT_SECRETS_FILE = "client_secrets.json"
STORAGE_FILE_NAME = "test"
LIVE_CHAT_REFRESH_RATE = 5

if __name__ == "__main__":
    service = yt.get_authenticated_service(CLIENT_SECRETS_FILE, STORAGE_FILE_NAME)
    
    live_broadcast = lb.choose_active_live_broadcast(service)
    
    if live_broadcast is None:
        exit("No active live broadcasts. ")
    
    print(live_broadcast)
    print(json.dumps(live_broadcast.__repr__(), indent=4))
    
    live_chat = lc.livechat_from_livebroascast(live_broadcast)
    
    print(live_chat)
    
    refresher = lc.LiveChatRefresher(live_chat, LIVE_CHAT_REFRESH_RATE)
    refresher.start()
    
    