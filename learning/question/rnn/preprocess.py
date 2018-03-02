import unidecode
import re

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
    
def featurize_sentences(sentences):
    """ Given a sentence, compte its feature vector and return it. """
    
    pass
    
def featurize(messages):
    pass
    
class Generator:
    pass
    
if __name__ == "__main__":
    message = "Alors, comment vous trouvez le video à date ? Avez vous des demandes particulieres ? N'hésitez pas ! 😃"
    
    print('\n'.join(prepare(message)))