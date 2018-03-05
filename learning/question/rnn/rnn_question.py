import re
import json
from configparser import ConfigParser

# To help with the command line interface
from argparse import ArgumentParser
import tkinter
from tkinter.filedialog import askopenfilename, asksaveasfilename

import numpy as np
import pandas as pd
from math import ceil

# Keras
from tensorflow.python.keras.utils import Sequence
from tensorflow.python.keras.models import Model, load_model
from tensorflow.python.keras.layers import Input, GRU, Dense, Dropout

# Package to replace accents by their non-accent equivalent
import unidecode

# Load config file
CONFIG_FILE = r'C:\Users\nicolas\GitHub\BlitzChat\learning\question\rnn\config.ini'
config = ConfigParser()
config.read(CONFIG_FILE)

# ======================= Preprocessing functions =============================

def prepare(messages):
    """ The preparation of the message consists of the following steps:
    1) Split the message into sentences (including punctuation)
    2) Remove all accents
    3) put the sentence to lower
    """

    if not isinstance(messages, list):
        messages = [messages]

    sentences = []
    for message in messages:
        message = unidecode.unidecode(message).lower().strip()
        pieces = re.split(r'(\.+|\?+|\!+)', message)
        for i in range(0, len(pieces), 2):
            sent = ''.join(pieces[i: i + 2]).strip()
            if len(sent) > 0 and sent not in sentences:
                sentences.append(sent)
    return sentences

def featurize_sentences(sentences, int_char_corr):
    """ Given sentences, compute their feature tensor and return it.
    Each feature tensor has shape (maxlen, num_vocab).
    """

    examples = np.zeros(
        (len(sentences), config.getint('data', 'maxlen'), int_char_corr.num_vocab)
    )

    for i, sent in enumerate(sentences):
        for j, c in enumerate(sent):
            examples[i, j, int_char_corr.to_int(c)] = 1

    return examples

def unfeaturize_examples(examples, int_char_corr):
    """ Given a collection of training examples for the model, tranform them back into regular sentences.
    """

    assert examples.shape[1:] == (config.getint('data', 'maxlen'), int_char_corr.num_vocab)

    sentences = []
    for example in examples:
        sentences.append(''.join(
                [int_char_corr.to_char(np.argmax(vec)) for vec in example]
            ).strip()
        )

    return sentences

def featurize_messages(messages, int_char_corr):
    """ Given messages, split them into sentences and featurize them. """

    return featurize_sentences(prepare(messages), int_char_corr)


class IntCharCorr:
    """ An object of this class does the job of translating characters into
    integers and vice-versa, according to the python dictionary passed to
    the constructor.
    """

    def __init__(self, intchar_file):
        with open(intchar_file, 'r') as f:
            self.intchar = json.load(f)

        self.charint = {c: i for i, c in self.intchar.items()}

    def to_int(self, char):
        """ Given a character, return the corresponding integer or 0 (which
        corresponds to the space character) if the character is not in the
        voacbulary.
        """

        return int(self.charint.get(char, 0))

    def to_char(self, int):
        """ Given an integer, return the corresponding character or the space character if the integer does not correspond to any known code.
        """

        return self.intchar.get(str(int), ' ')

    @property
    def num_vocab(self):
        """ Returns the number of characters in the vocabulary. """

        return len(self.intchar)

    def __repr__(self):
        return str(self.intchar)


class Generator(Sequence):
    """ A Generator object generates batches of training examples out of the training set.
    """

    def __init__(self, data_file,int_char_corr, batch_size=32):
        self.data_file = data_file
        self.int_char_corr = int_char_corr
        self.batch_size = batch_size

        self.train = pd.read_csv(data_file)
        self.sentences = self.train['sentences']
        self.labels = self.train['category']

    def __getitem__(self, idx):
        batch = featurize_sentences(
            self.sentences[idx*self.batch_size: (idx + 1)*self.batch_size],
            self.int_char_corr
        )

        return batch, self.labels[idx*self.batch_size: (idx + 1)*self.batch_size]

    def __len__(self):
        return ceil(len(self.sentences)/self.batch_size)

    def on_epoch_end(self):
        pass

    def __str__(self):
        return "Generator on training set {} with batch size {} and length {}".format(
            self.data_file,
            self.batch_size,
            len(self)
        )


# =========================== Defining function ===============================

def export_model(model_file):
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

    model.save(model_file)

# =========================== Training function ===============================

def train_model(trained_file, int_char_corr, epochs, batch_size):
    model = load_model(trained_file)

    generator = Generator(
        config['data']['trainset'],
        int_char_corr,
        batch_size=batch_size
    )

    checkpoint_file = os.path.join(
        config['training']['traineddir'],
        "{epoch:02d}-{loss:.4f}.hdf5"
    )

    checkpoint = ModelCheckpoint(
        checkpoint_file,
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


# ========================== Inference function ===============================

def infer_from_model(model, message):
    """ Given a message, featurize it and use the model to predict if it is
    a question or not.
    """

    return model.predict(featurize_messages(message, int_char_corr))


int_char_corr = IntCharCorr(config['data']['intchar'])

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument(
        'mode',
        help="Mode of the script. Choices are export, train, infer and select."
    )
    parser.add_argument(
        '--file',
        help="Name of a file."
    )
    parser.add_argument(
        '--epochs',
        type=int,
        default=1,
        help="Number of epochs to train the model."
    )
    parser.add_argument(
        '--batch_size',
        type=int,
        default=32,
        help="Batch size."
    )

    args = parser.parse_args()

    if args.mode == 'export':
        model_file = args.file
        if args.file is None:
            tkinter.Tk().withdraw()
            model_file = tkinter.filedialog.asksaveasfilename(
                title='Choose a file to save the model',
                defaultextension='hdf5',
                initialdir=config['DEFAULT']['basedir'],
                initialfile='model_definition'
            )
        export_model(model_file)
        print(">>> Model exported to {}".format(model_file))
    elif args.mode in ['train', 'infer', 'select']:
        trained_model_file = args.file
        if args.file is None:
            tkinter.Tk().withdraw()
            trained_model_file = tkinter.filedialog.askopenfilename(
                title='Select a model',
                defaultextension='hdf5',
                initialdir=config['model']['traineddir']
            )
        if args.mode == 'train':
            train_model(trained_model_file,int_char_corr, args.epochs, args.batch_size)
        elif args.mode == 'select':
            config['model']['bestmodel'] = trained_model_file
            with open(CONFIG_FILE, 'w') as configfile:
                config.write(configfile)
            print(">>> The new best model is {}".format(trained_model_file))
        else: # 'infer' mode
            model = load_model(config['model']['bestmodel'])
            while True:
                message = input("Your message: ")
                print(infer_from_model(model, message))
    else:
        print(">>> Invalid mode.")
else: # If the module is loaded, we load the best model
    model = load_model(config['model']['bestmodel'])
    
    def rnn_predict(message):
        return infer_from_model(model, message)