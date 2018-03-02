import re
import json
from configparser import ConfigParser
import tkinter
from tkinter.filedialog import askopenfilename, asksaveasfilename

# Third party package to replace accents by their non-accent equivalent
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
    """ Given sentences, compute their feature vector and return it. """
    
    pass
    
def featurize_messages(messages):
    """ Given messages, split them into sentences and compute the feature 
    vector of each sentence. """
    
    pass

class IntCharCorr:
    """ An object of this class does the job of translating characters into 
    integers and vice-versa, according to the python dictionary intchar 
    saved in the config.ini file.
    """
    
    def __init__(self):
        with open(config['data']['intchar'], 'r') as f:
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
    
class Generator:
    pass
    
if __name__ == "__main__":
    message = "Alors, comment vous trouvez le video à date ? Avez vous des demandes particulieres ? N'hésitez pas ! 😃"
    
    sent = prepare(message)[0]
    print(sent)
    
    intcharcorr = IntCharCorr()
    print("Number of characters in the vocabulary: {}".format(intcharcorr.num_vocab))
    print(''.join([
        intcharcorr.to_char(intcharcorr.to_int(c)) for c in message
    ]))