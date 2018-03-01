import numpy as np
import pandas as pd
import re
import json
import operator

from tensorflow.python.keras.preprocessing.text import Tokenizer

from tensorflow.python.keras.models import Sequential
from tensorflow.python.keras.layers import Dense

DATA_DIR = "..\\..\\drive-archive\\datasets\\material_questions\\full.csv"
DATA_COLUMN_NAMES = ['content', 'is_material_q']

TEST_TRAIN_SPLIT = 0.5

# Some hyperparameters
num_words = None
treshold = 1./25

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

def is_material_q(model, texts, treshold=treshold):
    features = tokenizer.texts_to_matrix(map(remove_floats, texts))
    prediction = model.predict(np.array(features))[0][0]
    return prediction >= treshold

def F1_score(model, x, y, treshold=treshold):
    predictions = model.predict(x) # floats
    predictions = np.array([1 if x >= treshold else 0 for x in predictions]) # binary

    true_pos, false_pos, false_neg, true_neg = 0, 0, 0, 0
    for i in range(y.shape[0]):
        if y[i] == 1:
            if predictions[i] == 1:
                true_pos += 1
            else:
                false_neg += 1
        else:
            if predictions[i] == 1:
                false_pos += 1
            else:
                true_neg += 1
                
    return 2*true_pos/(2*true_pos + false_pos + false_neg)
    
def classification(model, x, y, treshold=treshold):
    """ Given featurized questions x (i.e. a matrix of shape (batch, num_words))
    and the true labels, returns a table (string) of the results.
    """

    predictions = model.predict(x) # floats
    predictions = np.array([1 if x >= treshold else 0 for x in predictions]) # binary

    true_pos, false_pos, false_neg, true_neg = 0, 0, 0, 0
    for i in range(y.shape[0]):
        if y[i] == 1:
            if predictions[i] == 1:
                true_pos += 1
            else:
                false_neg += 1
        else:
            if predictions[i] == 1:
                false_pos += 1
            else:
                true_neg += 1

    table = """
                          Truth
                   |   Pos  |   Neg  |
    ----------------------------------
    Class  |  Pos  |  {:3}  |   {:3} |
           |  Neg  |  {:3}  |   {:3} |
    ----------------------------------
    """.format(true_pos, false_pos, false_neg, true_neg)

    return table


def precision(model, x, y, treshold=treshold):
    """ Given featurized questions x (i.e. a matrix of shape (batch, num_words))
    and the true labels, returns the precision of the model.
    """

    predictions = model.predict(x) # floats
    predictions = np.array([1 if x >= treshold else 0 for x in predictions]) # binary    
    true_pos = sum(y)

    true_pos, false_pos = 0, 0
    for i in range(y.shape[0]):
        if y[i] == 1:
            if predictions[i] == 1:
                true_pos += 1
        else:
            if predictions[i] == 1:
                false_pos += 1
    
    if true_pos + false_pos == 0:
        return np.nan
    else:
        return true_pos/(true_pos + false_pos)

def recall(model, x, y, treshold=treshold):
    """ Given featurized questions x (i.e. a matrix of shape (batch, num_words))
    and the true labels, returns the recall of the model.
    """

    predictions = model.predict(x) # floats
    predictions = np.array([1 if x >= treshold else 0 for x in predictions]) # binary

    true_pos, false_neg= 0, 0
    for i in range(y.shape[0]):
        if y[i] == 1:
            if predictions[i] == 1:
                true_pos += 1
            else:
                false_neg += 1
                
    if true_pos + false_neg == 0:
        return np.nan
    else:
        return true_pos/(true_pos + false_neg)



# Load all data
full_data = load_full_data()
full_data['content'] = full_data['content'].map(remove_floats)

# Preprocess data by extracting features
tokenizer = Tokenizer(num_words=num_words)
tokenizer.fit_on_texts(full_data['content'].tolist())

# for word in list(tokenizer.word_index.keys())[10:50]:
    # print("{}: {}".format(word, tokenizer.word_counts[word]))

# The design matrix, which has shape (samples, num_words)
features = tokenizer.texts_to_matrix(full_data['content'], mode='tfidf')

# Split the data into training and test sets
split = round(TEST_TRAIN_SPLIT*full_data.shape[0])
train_x = features[:split]
test_x  = features[split:]
train_y = np.array(full_data[DATA_COLUMN_NAMES[-1]][:split])
test_y  = np.array(full_data[DATA_COLUMN_NAMES[-1]][split:])

print("""Shapes:
train_x: {}
train_y: {}
test_x : {}
test_y : {}
""".format(train_x.shape[1], train_x.shape, train_y.shape, test_x.shape, test_y.shape, ))

# Build the model
model = Sequential()
#model.add(Dense(32, activation='relu', input_dim=num_words))
#model.add(Dense(1, activation='sigmoid'))
model.add(Dense(1, activation='sigmoid', input_dim=train_x.shape[1]))
model.compile(optimizer='adagrad',
              loss='binary_crossentropy',
              metrics=['accuracy'])

# Train the model
training = model.fit(
    train_x,
    train_y,
    epochs=20,
    batch_size=32,
    validation_split=0.2
)

# Compute the model's score
score = model.evaluate(test_x, test_y)
print("Metrics: {}".format(model.metrics_names))
print("Score: {}".format(score))
print(classification(model, test_x, test_y))

print("(Precision, Recall, F1) = ({}, {}, {})".format(
    precision(model, test_x, test_y),
    recall(model, test_x, test_y),
    F1_score(model, test_x, test_y)
))

F1scores = list(enumerate([
    F1_score(model, test_x, test_y, d/100.) for d in range(0, 100)
]))
F1scores.sort(key=operator.itemgetter(1))

print(F1scores[-1])

# Use the model
# while True:
    # message = input(">>> Input a message: ")
    # prediction = is_material_q(model, [message])
    # print("Prediction on \"{}\": {}".format(message, prediction))
