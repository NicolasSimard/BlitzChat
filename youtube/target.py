class Session:
    """ A Session is an object which represents a collection of chat messages
    that are processed and saved in a list.

    Attributes:
        messages: The list of mesages

    Methods:
        extend_messages: Extend the list of messages
        save: Save the session to pretty f json format
    """

    messages = []
    filters = []

    def __init__(self, print_messages=True):
        self.print_messages = print_messages

    def extend_messages(self, messages):
        """ Extend the messages with a list of ChatMessage objects.  """

        filtered = []
        for message in messages:
            filtered.append(message)
            # Apply the filters
            for filter in self.filters: filter(filtered[-1])
            # Maybe print the filtered message
            if self.print_messages: print(filtered[-1])
        self.messages.extend(filtered)

    def add_filter(self, f):
        self.filters.append(f)

    def save(self, file_name, mode='pretty'):
        """ Save the list of messages to the file named file_name. If the keyword
        parameter mode equals 'pretty' (default), the session is saved in pretty
        format. If the mode equals 'json', the messages are represented as
        dictionaries and saved in json format.
        """

        if len(self.messages) == 0: print(">>> The session is empty.")

        with open(file_name, 'w', encoding='utf-8') as f:
            if mode == 'pretty':
                string = '\n'.join([str(mess) for mess in self.messages])
                try:
                    f.write(string)
                except Exception as e:
                    print(">>> There was a problem with saving the session.")
                    print(e)
                else:
                    print(">>> Session succesfully saved.")
            elif mode == 'json':
                json_object = [mess.as_dict() for mess in self.messages]
                try:
                    json.dump(json_object, f, indent=4)
                except Exception as e:
                    print(">>> There was a problem with saving the session.")
                    print(e)
                else:
                    print(">>> Session succesfully saved.")
            else:
                print(">>> Unknown mode: {}".format(mode))

    def __repr__(self):
        return dict([
            ("messages", [message.__repr__() for message in self.messages])
        ]).__str__()

    def __str__(self):
        return("Chat object containing {} messages. ".format(len(self.messages)))


class Printer:
    def extend_messages(self, messages):
        for message in messages:
            print(message)

class MessageList:
    messages = []

    def __init__(self, target=None):
        self.target = target

    def extend_messages(self, messages):
        self.messages.extend(messages)
        if self.target is not None:
            self.target.extend_messages(messages)

    def __str__(self):
        return '\n'.join([message.__str__() for message in self.messages])
