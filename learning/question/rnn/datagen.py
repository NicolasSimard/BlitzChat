""" This script is meant to facilitate the process of generating data to
train the model out of raw data comming from youtube live chat ressources.
The script works at the level of ressource files. The task of generating
valid data for training is accomplished in two step (corresponding to the
two modes of the script):
Step 1: Prepare a raw json data file for labeling (mode '0')
Step 2: Append labeled data to the test and training set (mode '1')
The output of step 1 is a csv file with sentences labeled using the
default_label parameter of the prepare_for_labeling function. The user can
the open the csv file and change the label manually.
"""

from math import ceil
import json
import os
from configparser import ConfigParser
import pandas as pd
import tkinter
from tkinter.filedialog import askopenfilename, asksaveasfilename
from rnn_question import prepare

# Load local config file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, 'config.ini')
config = ConfigParser()
config.read(CONFIG_FILE)
config['DEFAULT']['basedir'] = BASE_DIR # basedir is needed by other variables

RESSOURCES_INCLUDED = os.path.join(config['data']['datadir'], 'ressources_included.json')

COLUMN = ['sentences', 'category']

def prepare_for_labeling(ressource_file, output_file, default_label=0):
    """ Takes a path to a youtube#liveChatMessage ressource_file (as
    produced when a LiveChat is saved to json), prepares the content of the
    messages, labels them using default_label and saves the resulting two
    column csv file to output_file.
    """

    with open(ressource_file, 'r', encoding='utf8') as f:
        ressources = json.load(f)

    messages = [
        ress['snippet']['textMessageDetails']['messageText']
        for ress in ressources
    ]

    unlabeled = pd.Series(prepare(messages), name=COLUMN[0])
    labels =    pd.Series([default_label]*len(unlabeled), name=COLUMN[1])

    pd.concat([unlabeled, labels], axis=1).to_csv(output_file, index=False)

def append_to_datasets(labeled_data):
    """ Given a csv file containing labeled data, appends this data to the
    train and test datasets.
    """

    with open(RESSOURCES_INCLUDED, 'r') as f:
        included = json.load(f)

    if labeled_data in included:
        print(">>> This labeled dataset has been marked as included.")
        if input(">>> Include it anyway? (Y)") != 'Y':
            print(">>> Exiting without appending the dataset.")
            return

    train = pd.read_csv(config['data']['trainset'])
    test = pd.read_csv(config['data']['testset'])
    print(">>> Before:\ntest: {}\ntrain: {}".format(test.shape, train.shape))

    new_data = pd.read_csv(labeled_data)
    print(">>> New data: {}".format(new_data.shape))

    questions = new_data.loc[new_data['category'] == 1]
    not_questions = new_data.loc[new_data['category'] == 0]

    questions_split = ceil(
        config.getfloat('training', 'testtrainsplit')*len(questions)
    )
    not_questions_split = ceil(
        config.getfloat('training', 'testtrainsplit')*len(not_questions)
    )

    # Split the questions
    test = test.append(questions.loc[:questions_split], ignore_index=True)
    train = train.append(questions.loc[questions_split:], ignore_index=True)

    # Split the non-questions
    test = test.append(not_questions.loc[:not_questions_split], ignore_index=True)
    train = train.append(not_questions.loc[not_questions_split:], ignore_index=True)

    print(">>> After:\ntest: {}\ntrain: {}".format(test.shape, train.shape))

    train.to_csv(config['data']['trainset'], index=False)
    test.to_csv(config['data']['testset'], index=False)

    print(">>> The data has been included in the test and training sets.")
    included.append(labeled_data)

    with open(RESSOURCES_INCLUDED, 'w') as f:
        json.dump(included, f, indent=4)

def shuffle_datasets():
    """ Loads the train and test datasets and shuffles them. """

    train = pd.read_csv(config['data']['trainset'])
    test = pd.read_csv(config['data']['testset'])

    train = train.sample(frac=1).reset_index(drop=True)
    test = test.sample(frac=1).reset_index(drop=True)

    train.to_csv(config['data']['trainset'], index=False)
    test.to_csv(config['data']['testset'], index=False)

def generate_intchar(intchar_file):
    train = pd.read_csv(config['data']['trainset'])
    test = pd.read_csv(config['data']['testset'])
    full = train.append(test, ignore_index=True)
    
    sent = full[COLUMN[0]]
    chars = sorted(list(set(''.join(sent))))
    corr = dict(list(enumerate(chars)))
    
    with open(intchar_file, 'w') as f:
        json.dump(corr, f, indent=4)
    
if __name__ == "__main__":
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('mode',
        help="Choose the mode of the script:\n"
        "shuffle: Shuffle the dataset;"
        "prepare: prepare raw data (from ressource) to be labeled;\n"
        "append: Incorporate labeled examples to the train and test datasets."
        "intchar: Generate an int-char bijection file.",
        default="shuffle"
    )
    args = parser.parse_args()

    if args.mode == "shuffle":
        shuffle_datasets()
    elif args.mode == "prepare":
        tkinter.Tk().withdraw()
        ressource_file = tkinter.filedialog.askopenfilename(
            title='Select ressource to prepare',
            defaultextension='json',
            initialdir=config['data']['datasrc']
        )

        initialfile = os.path.splitext(os.path.split(ressource_file)[1])[0]
        output_file = tkinter.filedialog.asksaveasfilename(
            title='Save data',
            defaultextension='csv',
            initialdir=config['data']['datadir'],
            initialfile=initialfile+'label_me'
        )

        prepare_for_labeling(ressource_file, output_file)
    elif args.mode == "append":
        tkinter.Tk().withdraw()
        labeled_data = tkinter.filedialog.askopenfilename(
            title='Select a file of labeled examples',
            defaultextension='csv',
            initialdir=config['data']['datadir']
        )

        append_to_datasets(labeled_data)
    elif args.mode == "intchar":
        tkinter.Tk().withdraw()
        intchar_file = tkinter.filedialog.asksaveasfilename(
            title='Choose a file to save the int-char correpondence',
            defaultextension='json',
            initialdir=config['data']['datadir'],
            initialfile='intchar.json'
        )

        generate_intchar(intchar_file)
    else:
        print(">>> invalid mode: {}".format(args.mode))