import time

from base.Exceptions import NeedReconnect, AlreadyHandledExceptions
from base.MessengerAPI import MessengerAPI

__author__ = 'JuniorJPDJ'


class MessengerPullParser(object):
    def __init__(self, msgapi, pulldelay=3):
        if not isinstance(msgapi, MessengerAPI):
            raise TypeError("'msgapi' has to be 'MessengerAPI.MessengerAPI', not '{}'".format(type(msgapi).__name__))
        self.lastpulltstamp = 0
        self.pulldelay = pulldelay
        self.msgapi = msgapi
        self.ms_type_handlers = {}

    def register_ms_type(self, typee, handler):
        assert callable(handler)
        assert isinstance(typee, (str, unicode))
        if typee in self.ms_type_handlers:
            raise AlreadyHandledExceptions
        else:
            self.ms_type_handlers[typee] = handler

    def make_pull(self):
        pulldelta = time.time() - self.lastpulltstamp
        if pulldelta < self.pulldelay:
            time.sleep(pulldelta + 0.1)
        try:
            data = self.msgapi.pull()
        except NeedReconnect:
            self.msgapi.send_reconnect()
            return
        self.lastpulltstamp = time.time()
        for i in data:
            if i['type'] in self.ms_type_handlers:
                self.ms_type_handlers[i['type']](i)
