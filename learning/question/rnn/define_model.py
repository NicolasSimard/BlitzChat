import json
from configparser import ConfigParser
import tkinter
from tkinter.filedialog import asksaveasfilename

from tensorflow.python.keras.models import Model
from tensorflow.python.keras.layers import Input, GRU, Dense, Dropout

from preprocess import int_char_corr

config = ConfigParser()
config.read('config.ini')

input = Input(shape = (None, int_char_corr.num_vocab))
gru_out = GRU(512)(input)
y = Dense(32, activation='relu')(gru_out)
y = Dropout(0.5)(y)
y = Dense(32, activation='relu')(y)
y = Dropout(0.5)(y)
output = Dense(1, activation='softmax')(y)

model = Model(input, output)

model.compile(
    loss='binary_crossentropy',
    optimizer='adagrad'
)

if __name__ == "__main__":
    print(model.summary())
    
    tkinter.Tk().withdraw()
    model_file = tkinter.filedialog.asksaveasfilename(
        title='Choose a file to save the model',
        defaultextension='hdf5',
        initialdir=config['DEFAULT']['basedir'],
        initialfile='model_definition'
    )
    
    model.save(model_file)