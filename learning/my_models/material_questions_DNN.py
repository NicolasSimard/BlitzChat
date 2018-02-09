import numpy as np
import pandas as pd
import re
import json

from tensorflow.python.keras.preprocessing.text import Tokenizer

from tensorflow.python.keras.models import Sequential
from tensorflow.python.keras.layers import Dense

DATA_DIR = "..\\..\\drive-archive\\datasets\\material_questions\\full.csv"
DATA_COLUMN_NAMES = ['content', 'is_material_q']

TEST_TRAIN_SPLIT = 0.8

# Some metaparameters
num_words = 75

def load_full_data():
    return pd.read_csv(DATA_DIR, names=DATA_COLUMN_NAMES, header=0)

def load_data(test_train_split=TEST_TRAIN_SPLIT):
    data = pd.read_csv(DATA_DIR, names=DATA_COLUMN_NAMES, header=0)
    
    split = round(test_train_split*data.shape[0])
    train = data[:split]
    test  = data[split:]
    
    train_x, train_y = train, train.pop(DATA_COLUMN_NAMES[-1])
    test_x, test_y = test, test.pop(DATA_COLUMN_NAMES[-1])
    return (train_x, train_y), (test_x, test_y)

def remove_floats(text):
    nbrs = re.compile(r'\d+')
    try:
        new_text = nbrs.sub(r'#', text)
    except TypeError as e:
        new_text = ""
    return new_text
    
# Load all data
full_data = load_full_data()
full_data['content'] = full_data['content'].map(remove_floats)

# Preprocess data by extracting features
tokenizer = Tokenizer(num_words=num_words)
tokenizer.fit_on_texts(full_data['content'].tolist())

# for word in list(tokenizer.word_index.keys())[10:50]:
    # print("{}: {}".format(word, tokenizer.word_counts[word]))

# The design matrix, which has shape (samples, num_words)
features = tokenizer.texts_to_matrix(full_data['content'], mode='binary')

# Split the data into training and test sets
split = round(TEST_TRAIN_SPLIT*full_data.shape[0])
train_x = features[:split]
test_x  = features[split:]
train_y = full_data[DATA_COLUMN_NAMES[-1]][:split]
test_y  = full_data[DATA_COLUMN_NAMES[-1]][split:]

print("""Shapes:
train_x: {}
train_y: {}
test_x : {}
test_y : {}
""".format(train_x.shape, train_y.shape, test_x.shape, test_y.shape, ))

# Build the model
model = Sequential()
model.add(Dense(32, activation='relu', input_dim=num_words))
model.add(Dense(1, activation='sigmoid'))
model.compile(optimizer='rmsprop',
              loss='binary_crossentropy',
              metrics=['accuracy'])

# Train the model              
training = model.fit(
    train_x,
    train_y,
    epochs=50,
    batch_size=32,
    validation_split=0.8
)

# Compute the model's score
score = model.evaluate(test_x, test_y)
print("Metrics: {}".format(model.metrics_names))
print("Score: {}".format(score))

# Use the model
while True:
    raw_message = input(">>> Input a message: ")
    message = tokenizer.texts_to_matrix([remove_floats(raw_message)])
    prediction = model.predict(np.array(message))
    print("Prediction on \"{}\": {}".format(raw_message, prediction))