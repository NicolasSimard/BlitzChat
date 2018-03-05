# For the window that prompts the user with a file_name
import tkinter
from tkinter.filedialog import askopenfilename, asksaveasfilename

import os
import json
from configparser import ConfigParser

from youtube.chat import *
from youtube.tools import get_authenticated_service
from youtube.filter import get_username, convert_to_local_time, question_labeler
from youtube.target import Session

# Read the config file
config = ConfigParser()
config.read('config.ini')

CREDENTIALS = "blitztutorat40"

if __name__ == "__main__":
    # Built a chat object
    session = Session()
    session.add_filter(convert_to_local_time)
    session.add_filter(question_labeler)

    # Create the mockchat
    tkinter.Tk().withdraw()
    ressources = tkinter.filedialog.askopenfilename(
        title='Select ressource',
        defaultextension='json',
        initialdir=config['DEFAULT']['archive']
    )
    mockchat = MockChat(ressources, session, speed=100) 
    print(mockchat)
    print("The chat should last {} seconds.".format(mockchat.duration))

    mockchat.start_refresh_loop()
    
    initialfile = os.path.splitext(os.path.split(ressources)[1])[0]
    save_file = tkinter.filedialog.asksaveasfilename(
        title='Save session',
        defaultextension='txt',
        initialdir=config['DEFAULT']['archive'],
        initialfile=initialfile
    )
    session.save(save_file)