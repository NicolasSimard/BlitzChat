from youtube.chat import ChatMessage
import json


if __name__ == "__main__":
    mess1 = ChatMessage(author = "Nick", published_at = "2017-12-01", content = "Truite")
    print("Before: ", mess1)
    
    with open("test.txt", 'w') as f:
        json.dump(mess1.__dict__, f)
    
    with open("test.txt", 'r') as f:
        mess1_dic = json.load(f)
    
    print(mess1_dic)
    
    print("After: ", ChatMessage(**mess1_dic))
    
    
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
    print("Before :", mess2)
    
    
    with open("test.txt", 'w') as f:
        json.dump(mess2.__dict__, f)
    
    with open("test.txt", 'r') as f:
        mess2_dic = json.load(f)
    
    print(mess2_dic)
    
    print("After: ", ChatMessage(**mess2_dic))
    
    