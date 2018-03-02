import re
import json
from configparser import ConfigParser
import tkinter
from tkinter.filedialog import askopenfilename, asksaveasfilename

import numpy as np
from tensorflow.python.keras.utils import Sequence

# Package to replace accents by their non-accent equivalent
import unidecode

config = ConfigParser()
config.read('config.ini')

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

    if not isinstance(sentences, list):
        sentences = [sentences]

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
    pass


int_char_corr = IntCharCorr(config['data']['intchar'])

if __name__ == "__main__":
    message = "Alors, comment vous trouvez le video à date ? Avez vous des demandes particulieres ? N'hésitez pas ! 😃"

    sent = prepare(message)[0]
    print(sent)

    print("Number of characters in the vocabulary: {}".format(int_char_corr.num_vocab))
    print(''.join([
        int_char_corr.to_char(int_char_corr.to_int(c)) for c in sent
    ]))

    sent = "Alors, comment vous trouvez le video à date ?"
    print(sent)
    example = featurize_sentences(sent, int_char_corr)
    print(unfeaturize_examples(example, int_char_corr))
    
    print(featurize_messages(message, int_char_corr).shape)