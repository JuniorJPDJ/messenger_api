__author__ = 'JuniorJPDJ'


class NeedReconnectBeforePull(Exception):
    pass

class LoggingInError(Exception):
    pass

class MessengerException(Exception):
    def __init__(self, id, summary, description):
        super(MessengerException, self).__init__(u"{}: {} ({})".format(summary, description, id))
        self.id = id
        self.summary = summary
        self.description = description

class WTFException(Exception):
    pass
