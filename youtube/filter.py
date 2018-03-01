import dateutil
from dateutil.parser import parse
import re

from .tools import get_channel_title, delete_message

def question_labeler(message):
    if "?" in message.content:
        message.add_label("Q")

def get_username(client):
    titles = {}
    
    def f(message):
        if message.author_channel_id in titles:
            message.author = titles[message.author_channel_id]
        else:
            title = get_channel_title(client, message.author_channel_id)
            titles[message.author_channel_id] = title
            message.author = title
    return f

def delete_pattern(client, pattern):
    pattern = re.compile(pattern)
    
    def f(message):
        if pattern.search(message.content) is not None:
            delete_message(client, message.id)
            
    return f

    
def convert_to_local_time(message):
    dt = parse(message.published_at)
    message.published_at = str(dt.astimezone(dateutil.tz.tzlocal()))