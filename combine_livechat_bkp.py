from youtube.chat import combine_live_chat_backups_in_dir

import tkinter
from tkinter.filedialog import asksaveasfilename, askdirectory

tkinter.Tk().withdraw()
print(">>> Choose the directory containing the backup files.")
dir = tkinter.filedialog.askdirectory(title="Choose backup directory")

print(">>> Choose where youtu want to save the combined ressource.")
file_name = tkinter.filedialog.asksaveasfilename(title="Choose ressource save location")

combine_live_chat_backups_in_dir(dir, file_name)

