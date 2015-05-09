__author__ = 'juniorjpdj'

import time, datetime
from collections import deque
from MessengerAttachmentsAPI import Attachment


class MessengerRealTimeChat(object):
    def __init__(self, messenger):
        self.handled_msgs = deque(maxlen=30)
        self.lastpull = 0
        self.pullsleep = 3
        self.group_msg_handlers = set()
        self.msg_handlers = set()
        self.own_group_msg_handlers = set()
        self.own_msg_handlers = set()
        self.messenger = messenger
        self.messenger.send_reconnect()
        self.friends = self.messenger.get_friends()

    def register_group_msg_handler(self, handler):
        # group_msg_handler(datetime, (sender_id, sender_name), (group_id, group_name), message_body, a)
        self.group_msg_handlers.add(handler)

    def register_msg_handler(self, handler):
        # msg_handler(datetime, (sender_id, sender_name), message_body, a)
        self.msg_handlers.add(handler)

    def register_own_group_msg_handler(self, handler):
        # own_group_msg_handler(datetime, (group_id, group_name), message_body, a)
        self.own_group_msg_handlers.add(handler)

    def register_own_msg_handler(self, handler):
        # own_msg_handler(datetime, (user_id, user_name), message_body, a)
        self.own_msg_handlers.add(handler)

    def make_pull(self):
        pulldelta = time.time() - self.lastpull
        if pulldelta < self.pullsleep:
            time.sleep(pulldelta + 0.1)
        data = self.messenger.send_pull()
        self.lastpull = time.time()
        if data:
            for i in data:
                if i['type'] == 'messaging' and i['event'] == 'deliver':
                    m = i['message']
                    a = m['attachments'] if m['has_attachment'] else []
                    a = tuple(map(lambda a: Attachment(a), a))
                    if m['mid'] not in self.handled_msgs:
                        self.handled_msgs.append(m['mid'])
                        if str(m['sender_fbid']) == self.messenger.uid:
                            if 'group_thread_info' in m and m['group_thread_info']:
                                for h in self.own_group_msg_handlers:
                                    h(datetime.datetime.fromtimestamp(int(m['timestamp']) / 1000.0), (int(m['thread_fbid']), unicode(m['group_thread_info']['name'])), unicode(m['body']), a)
                            else:
                                for h in self.own_msg_handlers:
                                    user = int(m['other_user_fbid'])
                                    h(datetime.datetime.fromtimestamp(int(m['timestamp']) / 1000.0), (user, unicode(self.friends[user]['name'] if user in self.friends else 'Me' if user == int(self.messenger.uid) else '')), unicode(m['body']), a)
                        elif 'group_thread_info' in m and m['group_thread_info']:
                            for h in self.group_msg_handlers:
                                h(datetime.datetime.fromtimestamp(int(m['timestamp']) / 1000.0), (int(m['sender_fbid']), unicode(m['sender_name'])), (int(m['thread_fbid']), unicode(m['group_thread_info']['name'])), unicode(m['body']), a)
                        elif m['other_user_fbid'] == m['sender_fbid']:
                            for h in self.msg_handlers:
                                h(datetime.datetime.fromtimestamp(int(m['timestamp']) / 1000.0), (int(m['sender_fbid']), unicode(m['sender_name'])), unicode(m['body']), a)
                else:
                    pass
                    # comming soon :D