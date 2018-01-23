import threading
import os
import json

class Printer(threading.Thread):
    def __init__(self, source):
        super().__init__(name="Printer thread.")
        self.source = source

    def run(self):
        bookmark = 0
        while not self.source.is_over.is_set():
            with self.source.has_new_messages:
                self.source.has_new_messages.wait()
                response = self.source.get_messages_next(bookmark)
                bookmark = response.get("index", 0)
                for message in response.get("items", []):
                    print(message.__str__())


class LiveBackUp(threading.Thread):
    """ Save a Chat object periodically to a given file. This is for back-up
    purposes. To save a whole Chat object, just use its save method.

    Attribute:
        source              The source of chat messages
        target_dir          The directory in which the Saver objects saves
        buffer_size         Size of the buffer
    """

    def __init__(self, source, target_dir, buffer_size=50):
        """ Initialize the LiveSaver object with a source and a target
        directory target_dir. The buffer_size parameter is the size of the
        buffer."""

        super().__init__(name="LiveSaver thread.")
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

    def run(self):
        bookmark = 0
        while not self.source.is_over.is_set():
            with self.source.has_new_messages:
                self.source.has_new_messages.wait()
                response = self.source.get_messages_next(bookmark)
                bookmark = response.get("index", 0)
                self._buffer.extend(response.get("items", []))

                if len(self._buffer) >= self.buffer_size:
                    self.dump_buffer()

        if len(self._buffer) > 0:
            self.dump_buffer()
            
        print(">>> Closing LiveBackUp object after {} backup.".format(
            self._bkp_count)
        )


def archive(source, target):
    """ Save a Chat object to a python shelve. """
    pass