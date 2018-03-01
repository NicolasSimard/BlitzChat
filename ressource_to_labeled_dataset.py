""" This file iterates over the messages in the RESSOURCE_FILE and asks the
user to label them. Those labeled messages are then saved in the DATASET_DIR.
"""

import json
import os
import numpy as np
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESSOURCE_FILE = os.path.join(BASE_DIR, "drive-archive", "ressources", "2017-12-12-1(reconstructed).json")
DATASET_DIR    = os.path.join(BASE_DIR, "drive-archive", "datasets", "test")

# Initializing the session
try:
    os.mkdir(DATASET_DIR)
except FileExistsError as e:
    pass
else:
    print(">>> Directory {} created.".format(DATASET_DIR))

# The labels
LABELS = [
    "question",
    "not_question"
]

# Load the ressource
with open(RESSOURCE_FILE, 'r') as f:
    ressource = json.load(f)
    
# Create the (unlabeled) dataset out of the ressource
data = pd.Series(
    [mess['content'] for mess in ressource],
    name='content'
)

# # Label the elements of the dataset
# labels   = pd.Series(
    # [1 if mess['classification'][2] == 1 else 0 for mess in ressource],
    # name="category"
# )

labels = []
for message in data:
    print(message)
    try:
        label = int(input())
    except ValueError:
        label = 0
    labels.append(label)

pd.concat([data, pd.Series(labels, name='labels')], axis=1).to_csv(os.path.join(DATASET_DIR, "full.csv"))
