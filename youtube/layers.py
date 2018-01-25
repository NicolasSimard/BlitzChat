import threading
import os
import json
import re

#TODO: A layer to convert the time from UTC to local. 
#NOTE:  To convert the string s='2018-01-16T16:31:12.000Z' to a datetime
#       object: dt = dateutil.parser.parse(s). The tzinfo will be tzutc()
#       Given such a UTC time dt, you can convert it to a local time:
#       >>> dt = dateutil.parser.parse(s); dt
#       datetime.datetime(2018, 1, 16, 16, 31, 12, tzinfo=tzutc())
#       >>> dt.astimezone(dateutil.tz.tzlocal())
#       datetime.datetime(2018, 1, 16, 11, 31, 12, tzinfo=tzlocal())
#TODO: A layer to replace th eauthorChannelId with something like 'User n'
#TODO: A layer to detect exam questions


class Layer(threading.Thread):
    """ Defines an abstract layer in the processing pipe of chat messages.
    """

    has_new_messages = threading.Condition()
    index = 0

    def __init__(self, chat, source, name, **kwargs):
        super().__init__(name=name)
        self.source = source
        self.is_over = source.is_over
        self.chat = chat
        self.timeout = kwargs.get("timeout", 5)

    def action(self, message):
        print("The Layer.action method should be overriden.")

    def last_action(self):
        pass

    def run(self):
        while not self.source.is_over.is_set():
            with self.source.has_new_messages:
                has_been_notified = self.source.has_new_messages.wait(self.timeout)
                if has_been_notified:
                    new_messages = self.chat.get_messages(self.index, self.source.index)
                    for message in new_messages:
                        self.action(message)
                    self.index = self.source.index
                    with self.has_new_messages:
                        self.has_new_messages.notify_all()
        self.last_action()
        print(">>> Closing Layer {}".format(self.name))

    def __repr__(self):
        return "Layer {}.".format(self.name)


class Question(Layer):
    def __init__(self, chat, source):
        super().__init__(chat, source, name = "naive question detector")

    def action(self, message):
        if "?" in message.content:
            message.add_label("Q")


class Printer(Layer):
    def __init__(self, chat, source):
        super().__init__(chat, source, name = "printer")

    def action(self, message):
        print(message)


class LiveBackUp(Layer):
    """ Save a Chat object periodically to a given file. This is for back-up
    purposes. To save a whole Chat object, just use its save method.

    Attribute:
        source              The source of chat messages
        target_dir          The directory in which the Saver objects saves
        buffer_size         Size of the buffer
    """

    def __init__(self, chat, source, target_dir, buffer_size=10):
        """ Initialize the LiveSaver object with a source and a target
        directory target_dir. The buffer_size parameter is the size of the
        buffer."""

        super().__init__(chat, source, name = "live back up")
        self.buffer_size = buffer_size
        self.source = source
        if not os.path.exists(target_dir):
            print("Auto making directory: {}".format(target_dir))
            os.makedirs(target_dir)
        self.target_dir = target_dir
        self._buffer = []
        self._bkp_count = 0

    def dump_buffer(self):
        """ Dump the buffer in the file self.target_dir. """
        self._bkp_count += 1
        file_name = "auto_bkp_{}.bkp".format(self._bkp_count)
        target_file = os.path.join(self.target_dir, file_name)
        with open(target_file, 'w') as f:
            L = [message.__repr__() for message in self._buffer]
            json.dump(L, f)
        self._buffer = []

    def action(self, message):
        self._buffer.append(message)

        if len(self._buffer) >= self.buffer_size:
            self.dump_buffer()

    def last_action(self):
        self.dump_buffer()
