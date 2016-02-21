__author__ = 'JuniorJPDJ'


class NeedReconnect(Exception):
    pass


class LoggingInError(Exception):
    pass


class MessengerException(Exception):
    def __init__(self, eid, summary, description):
        super(MessengerException, self).__init__(u"{}: {} ({})".format(summary, description, eid))
        self.id = eid
        self.summary = summary
        self.description = description


class WTFException(Exception):
    pass


class UserNotFoundException(Exception):
    pass


class UnknownDictFormatException(Exception):
    pass


class UnknownThreadException(Exception):
    pass


class UnknownPersonException(Exception):
    pass
