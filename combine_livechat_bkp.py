from youtube.chat import combine_live_chat_backups_in_dir

import tkinter
from tkinter.filedialog import asksaveasfilename, askdirectory
from configparser import ConfigParser

# Read the config file
config = ConfigParser()
config.read('config.ini')

tkinter.Tk().withdraw()
print(">>> Choose the directory containing the backup files.")
dir = tkinter.filedialog.askdirectory(
    title="Choose backup directory",
    initialdir=config['livechat']['backup']
)

print(">>> Choose where you want to save the combined ressource.")
file_name = tkinter.filedialog.asksaveasfilename(
    title='Save LiveChat',
    defaultextension='json',
    initialdir=config['DEFAULT']['archive']
)
combine_live_chat_backups_in_dir(dir, file_name)

