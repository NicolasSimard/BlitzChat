import threading

class Printer(threading.Thread):
    def __init__(self, source, name=None):
        super().__init__(name=name)
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