# For the window that prompts the user with a file_name
import tkinter
from tkinter.filedialog import askopenfilename, asksaveasfilename

import os
import json

from youtube.chat import Chat, MockChat
from youtube.target import Printer, MessageList, MessageFilter
from youtube.filter import question_labeler

tkinter.Tk().withdraw()
file_name = tkinter.filedialog.askopenfilename(title="Open MockChat")

# mockchat = MockChat(file_name, Printer(), speed=100)
message_list = MessageList(target=Printer())

message_filter = MessageFilter(target=message_list)
message_filter.add_filter(question_labeler)

mockchat = MockChat(file_name, message_filter, speed=100) 
print(mockchat)
print("The chat should last {} seconds.".format(mockchat.duration))

print(message_filter)

mockchat.start()
mockchat.join()