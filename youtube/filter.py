import dateutil
from dateutil.parser import parse

from .tools import get_channel_title

def question_labeler(message):
    if "?" in message.content:
        message.add_label("Q")

def get_username(client):
    titles = {}
    
    def f(message):
        if message.author in titles:
            message.author = titles[message.author]
        else:
            title = get_channel_title(client, message.author)
            titles[message.author] = title
            message.author = title
    return f
    
def convert_to_local_time(message):
    dt = parse(message.published_at)
    message.published_at = str(dt.astimezone(dateutil.tz.tzlocal()))