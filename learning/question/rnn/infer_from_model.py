import tkinter
from tkinter.filedialog import askopenfilename, asksaveasfilename
from configparser import ConfigParser

from tensorflow.python.keras.models import Model, load_model
from tensorflow.python.keras.layers import Input, GRU, Dense, Dropout
from tensorflow.python.keras.callbacks import ModelCheckpoint, Callback

from preprocess import featurize_messages, int_char_corr

config = ConfigParser()
config.read('config.ini')

model = load_model(config['model']['bestmodel'])

def predict_question(message):
    """ Given a message, featurize it and use the model to predict if it is 
    a question or not.
    """
    
    return model.predict(featurize_messages(message, int_char_corr))
    
if __name__ == "__main__":
    message = "Alors, comment vous trouvez le video à date ? Avez vous des demandes particulieres ? N'hésitez pas ! 😃"
    
    print(predict_question(message))