import time

from .base.Exceptions import NeedReconnect
from .Actions import Action

__author__ = 'JuniorJPDJ'


class MessengerPullParser(object):
    def __init__(self, msg, pulldelay=3):
        self._lastpulltstamp = 0
        self.pulldelay = pulldelay
        self.msg = msg
        self._action_handlers = set()

    def register_actions_handler(self, handler):
        assert callable(handler)
        self._action_handlers.add(handler)

    def make_pull(self):
        pulldelta = time.time() - self._lastpulltstamp
        if pulldelta < self.pulldelay:
            time.sleep(pulldelta + 0.1)
        try:
            data = self.msg.msgapi.pull()
        except NeedReconnect:
            self.msg.msgapi.send_reconnect()
            return
        self._lastpulltstamp = time.time()
        for i in data:
            a = Action.from_pull(self.msg, i)
            if a is None:
                continue
            elif isinstance(a, tuple):
                for ac in a:
                    for h in self._action_handlers:
                        h(ac)
            else:
                for h in self._action_handlers:
                    h(a)
