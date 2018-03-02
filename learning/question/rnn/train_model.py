import os
import sys
import json
from configparser import ConfigParser
import tkinter
from tkinter.filedialog import askopenfilename

from tensorflow.python.keras.models import Model, load_model
from tensorflow.python.keras.layers import Input, GRU, Dense, Dropout
from tensorflow.python.keras.callbacks import ModelCheckpoint, Callback

from preprocess import Generator, int_char_corr

config = ConfigParser()
config.read('config.ini')

CHECKPOINT_FILE = os.path.join(
    config['training']['traineddir'],
    "{epoch:02d}-{loss:.4f}.hdf5"
)

generator = Generator(config['data']['trainset'], int_char_corr, batch_size=100)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        epochs = int(sys.argv[1])
    else:
        epochs = 1

    tkinter.Tk().withdraw()
    trained_model = tkinter.filedialog.askopenfilename(
        title='Select a model to train',
        defaultextension='hdf5',
        initialdir=config['training']['traineddir']
    )
    
    model = load_model(trained_model)
    
    checkpoint = ModelCheckpoint(
        CHECKPOINT_FILE,
        monitor='loss',
        verbose=1,
        save_best_only=True,
        mode='min'
    )
    callbacks_list = [checkpoint]

    print(">>> Training model for {} epochs.".format(epochs))
    
    model.fit_generator(
        generator,
        steps_per_epoch=len(generator),
        epochs=epochs,
        callbacks=callbacks_list
    )