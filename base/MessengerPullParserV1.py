import datetime
import logging
import time
from collections import deque, defaultdict

from Attachments import Attachment
from base.Exceptions import WTFException
from base.MessengerAPI import MessengerAPI

try:
    unicode()
except NameError:
    unicode = str  # python3 support

__author__ = 'JuniorJPDJ'

# DONE: rewrite for using handlers for action types, not if/elif for each one (v2)
# This file stays here only for compatibility reasons


class MessengerPullParser(object):
    def __init__(self, messenger):
        if not isinstance(messenger, MessengerAPI):
            raise TypeError("'messenger' has to be 'MessengerAPI.MessengerAPI', not '{}'".format(type(messenger).__name__))
        self.handled_msgs = deque(maxlen=30)
        self.lastpull = 0
        self.pullsleep = 3
        self.handlers = defaultdict(set)
        self.messenger = messenger
        self.messenger.send_reconnect()
        self.friends = self.messenger.get_all_users_info()

    handler_types = ('group_msg', 'msg', 'own_group_msg', 'own_msg', 'group_leave', 'group_kick', 'group_add',
                     'group_rename', 'group_change_avatar', 'group_read', 'read', 'group_started_typing',
                     'group_stopped_typing', 'started_typing', 'stopped_typing', 'thread_color_theme_change',
                     'thread_participant_nickname_change', 'delivery')

    def register_handler(self, htype, handler):
        # group_msg_handler(datetime, (sender_id, sender_name), (group_id, group_name), message_body, attachment)
        # msg_handler(datetime, (sender_id, sender_name), message_body, attachment)
        # own_group_msg_handler(datetime, (group_id, group_name), message_body, attachment)
        # own_msg_handler(datetime, (user_id, user_name), message_body, attachment)
        # group_leave_handler(datetime, (user_id, user_name), (group_id, group_name))
        # group_kick_handler(datetime, (kicker_id, kicker_name), (user_id, user_name), (group_id, group_name))
        # group_add_handler(datetime, (adder_id, adder_name), (user_id, user_name), (group_id, group_name))
        # group_rename_handler(datetime, performer_id, group_id, new_group_name)
        # group_change_avatar_handler(datetime, performer_id, group_id, avatar)
        # read_handler(datetime, reader)
        # group_read_handler(datetime, group_id, reader)
        # group_started_typing_handler(datetime, group_id, user_id)
        # group_stopped_typing_handler(datetime, group_id, user_id)
        # started_typing_handler(datetime, from_id)
        # stopped_typing_handler(datetime, from_id)
        # thread_color_theme_change_handler(datetime, thread_id, author_id, color)
        # thread_participant_nickname_change_handler(datetime, thread_id, author_id, participant_id, nickname)
        # delivery_handler(datetime, thread_id)
        assert htype in self.handler_types
        assert callable(handler)
        self.handlers[htype].add(handler)

    def make_pull(self):
        pulldelta = time.time() - self.lastpull
        if pulldelta < self.pullsleep:
            time.sleep(pulldelta + 0.1)
        data = self.messenger.pull()
        self.lastpull = time.time()
        for i in data:
            if i['type'] == 'messaging':
                if i['event'] == 'deliver':
                    # there is message incomming
                    m = i['message']
                    a = m['attachments'] if m['has_attachment'] else []
                    a = tuple([Attachment.from_dict(at) for at in a])
                    timestamp = datetime.datetime.fromtimestamp(int(m['timestamp']) / 1000.0)
                    if m['mid'] not in self.handled_msgs:
                        self.handled_msgs.append(m['mid'])
                        if str(m['sender_fbid']) == self.messenger.uid:
                            # sent by me
                            if 'group_thread_info' in m and m['group_thread_info']:
                                # to group
                                for h in self.handlers['own_group_msg']:
                                    h(timestamp, (int(m['thread_fbid']), unicode(m['group_thread_info']['name'])), unicode(m['body']), a)
                            else:
                                # to someone
                                for h in self.handlers['own_msg']:
                                    user = int(m['other_user_fbid'])
                                    h(timestamp, (user, unicode(self.friends[user]['name'] if user in self.friends else 'Me' if user == int(self.messenger.uid) else '')), unicode(m['body']), a)
                        elif 'group_thread_info' in m and m['group_thread_info']:
                            # sent by someone to group
                            for h in self.handlers['group_msg']:
                                h(timestamp, (int(m['sender_fbid']), unicode(m['sender_name'])), (int(m['thread_fbid']), unicode(m['group_thread_info']['name'])), unicode(m['body']), a)
                        elif m['other_user_fbid'] == m['sender_fbid']:
                            # sent by someone to me
                            for h in self.handlers['msg']:
                                h(timestamp, (int(m['sender_fbid']), unicode(m['sender_name'])), unicode(m['body']), a)
                elif i['event'] == 'delivery_receipt' and i['delivered'] == True:
                    # delivered to someone
                    for h in self.handlers['delivery']:
                        h(datetime.datetime.fromtimestamp(int(i['timestamp'])), i['thread_fbid'])
                elif i['event'] == 'read_receipt':
                    timestamp = datetime.datetime.fromtimestamp(int(i['time']) / 1000.0)
                    if 'thread_fbid' in i:
                        # read in group
                        for h in self.handlers['group_read']:
                            h(timestamp, i['thread_fbid'], i['reader'])
                    else:
                        # read in private chat
                        for h in self.handlers['read']:
                            h(timestamp, i['reader'])
            elif i['type'] == 'update_multichat_participants':
                timestamp = datetime.datetime.fromtimestamp(int(i['timestampMsec']) / 1000.0)
                if i['actionType'] == 1:
                    # someone was added to group
                    for u in i['newRecipientsInfo'].values():
                        for h in self.handlers['group_add']:
                            h(timestamp, (i['actorInfo']['fbid'], i['actorInfo']['name']), (u['fbid'], u['name']), (int(i['id'][3:]), i['nub_name']['__html']))
                elif i['actionType'] == 2:
                    # someone left group
                    for u in i['newRecipientsInfo'].values():
                        if u['fbid'] == i['actorInfo']['fbid']:
                            for h in self.handlers['group_leave']:
                                h(timestamp, (u['fbid'], u['name']), (i['id'][3:], i['nub_name']['__html']))
                        else:
                            for h in self.handlers['group_kick']:
                                h(timestamp, (i['actorInfo']['fbid'], i['actorInfo']['name']), (u['fbid'], u['name']), (int(i['id'][3:]), i['nub_name']['__html']))
                else:
                    raise WTFException()
            elif i['type'] == 'ttyp':
                if i['st']:
                    # someone started typing at group chat
                    for h in self.handlers['group_started_typing']:
                        h(datetime.datetime.now(), i['thread_fbid'], i['from'])
                else:
                    # someone stopped typing at group chat
                    for h in self.handlers['group_stopped_typing']:
                        h(datetime.datetime.now(), i['thread_fbid'], i['from'])
            elif i['type'] == 'typ':
                if i['st']:
                    # someone started typing at private chat
                    for h in self.handlers['started_typing']:
                        h(datetime.datetime.now(), i['from'])
                else:
                    # someone stopped typing at private chat
                    for h in self.handlers['stopped_typing']:
                        h(datetime.datetime.now(), i['from'])
            elif i['type'] == 'mercury':
                # protocol in protocol, I love U Facebook <3
                for a in i['actions']:
                    timestamp = datetime.datetime.fromtimestamp(int(a['timestamp']) / 1000.0)
                    if a['action_type'] == 'ma-type:log-message':
                        if a['log_message_type'] == 'log:thread-name':
                            # group rename
                            for h in self.handlers['group_rename']:
                                h(timestamp, a['author'][5:], a['thread_fbid'], a['log_message_data']['name'])
                        elif a['log_message_type'] == 'log:thread-image':
                            # group avatar change
                            avatar = Attachment.from_dict(a['log_message_data']['image'])
                            for h in self.handlers['group_change_avatar']:
                                h(timestamp, a['author'][5:], a['thread_fbid'], avatar)
                        elif a['log_message_type'] == 'log:generic-admin-text':
                            # u serious fb? -.-
                            if a['log_message_data']['message_type'] == 'change_thread_theme':
                                # color theme change
                                for h in self.handlers['thread_color_theme_change']:
                                    h(timestamp, a['thread_fbid'], a['author'][5:], a['log_message_data']['untypedData']['theme_color'])
                            elif a['log_message_data']['message_type'] == 'change_thread_nickname':
                                # participant nickname change
                                for h in self.handlers['thread_participant_nickname_change']:
                                    h(timestamp, a['thread_fbid'], a['author'][5:], a['log_message_data']['untypedData']['participant_id'], a['log_message_data']['untypedData']['nickname'])
            elif i['type'] == 'buddylist_overlay':
                # NOPE: make use of buddylist_overlay (won't be done, I'm no longer developing this file)
                pass
            elif i['type'] in ('delta', 'deltaflow', 'inbox', 'm_read_receipt'):
                # wut is delta and deltaflow?
                # oh, fuck it, I don't need it anyway
                # PS. If u know what it does, pls send me info
                pass
            else:
                logging.debug('Something not handled in messenger protocol')
                logging.debug(i)
