from youtube.chat import ChatMessage, Chat
import json
import os

if __name__ == "__main__":
    mess1 = ChatMessage(author = "Nick", published_at = "2017-12-01", content = "Truite")

    youtube_mess = {
                "type": "textMessageEvent",
                "liveChatId": "Cg0KC1lxVHZfaC1CempZ",
                "authorChannelId": "UC7aeSVebvKLp4o5MLtq5LZg",
                "publishedAt": "2018-01-09T21:52:33.028Z",
                "hasDisplayContent": True,
                "displayMessage": "Allo",
                "textMessageDetails": {
                    "messageText": "Allo"
                }
    }
    
    mess2 = ChatMessage(**youtube_mess)
    
    chat = Chat()
    chat.extend_messages([mess1, mess2])
    print(chat)
    print(chat.__dict__)
    
    chat.save_to_json(os.path.dirname(os.path.abspath(__file__)))
    
    