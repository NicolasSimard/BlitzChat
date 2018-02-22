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
        
class MessageFilter:
    """ A MessageFilter object applies a series of filters to incoming messages. Each filter should be a callable object (e.g. a function) which takes a ChatMessage as input and modifies it."""

    filters = []

    def __init__(self, target='print'):
        self.target = target
    
    def extend_messages(self, messages):
        filtered = []
        for message in messages:
            filtered.append(message)
            # Apply the filters
            for filter in self.filters: filter(filtered[-1])
        if self.target == 'print':
            for message in filtered:
                print(message)
        else:
            self.target.extend_messages(filtered)
            
    def add_filter(self, filter):   
        """ Add a filter. """
        
        self.filters.append(filter)
        
    def __str__(self):
        return 'MessageFilter with filters {}.'.format(self.filters)
            