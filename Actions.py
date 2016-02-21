from Message import Message
from Attachments import Attachment
from datetime import datetime

__author__ = 'JuniorJPDJ'

# TODO: emoticon change action
# TODO: buddylist_overlay action
# TODO: from_thread_info


class Action(object):
    def __init__(self, msg):
        self.msg = msg
        
    @classmethod
    def unknown(cls, msg, data):
        f = cls(msg)
        f.data = data
        return f

    @classmethod
    def from_pull(cls, msg, data):
        if data['type'] == 'messaging':
            if data['event'] == 'deliver':
                return Message.from_pull(msg, data['message'])
            elif data['event'] == 'delivery_receipt' and data['delivered'] == True:
                return DeliveryAction.from_pull(msg, data)
            elif data['event'] == 'read_receipt':
                return ReadAction.from_pull(msg, data)
            else:
                return Action.unknown(msg, data)
        elif data['type'] in ('ttyp', 'typ'):
            return TypingAction.from_pull(msg, data)
        elif data['type'] == 'mercury':
            out = []
            for a in data['actions']:
                if a['action_type'] == 'ma-type:log-message':
                    if a['log_message_type'] == 'log:subscribe':
                        out.append(ThreadParticipantAddAction.from_pull(msg, a))
                    elif a['log_message_type'] == 'log:unsubscribe':
                        if len(a['log_message_data']['removed_participants']) == 1 and a['log_message_data']['removed_participants'][0] == a['author']:
                            out.append(ThreadParticipantLeaveAction.from_pull(msg, a))
                        else:
                            out.append(ThreadParticipantKickAction.from_pull(msg, a))
                    elif a['log_message_type'] == 'log:thread-name':
                        out.append(ThreadRenameAction.from_pull(msg, a))
                    elif a['log_message_type'] == 'log:thread-image':
                        out.append(ThreadImageChangeAction.from_pull(msg, a))
                    elif a['log_message_type'] == 'log:generic-admin-text':
                        if a['log_message_data']['message_type'] == 'change_thread_theme':
                            out.append(ThreadThemeColorChangeAction.from_pull(msg, a))
                        elif a['log_message_data']['message_type'] == 'change_thread_nickname':
                            out.append(ThreadParticipantNameChangeAction.from_pull(msg, a))
                        else:
                            out.append(Action.unknown(msg, a))
                    else:
                        out.append(Action.unknown(msg, a))
                else:
                    out.append(Action.unknown(msg, a))
            return tuple(out)
        else:
            return Action.unknown(msg, data)

    @classmethod
    def from_thread_info(cls, thread, data):
        pass


class ThreadParticipantLeaveAction(Action):
    def __init__(self, msg, time, thread, person, mid, body):
        Action.__init__(self, msg)
        self.time, self.thread, self.person, self.mid, self.body = time, thread, person, mid, body

    @classmethod
    def from_pull(cls, msg, data):
        return cls(msg, datetime.fromtimestamp(data['timestamp'] / 1000.0), msg.get_thread(int(data['thread_fbid'])), msg.get_person(int(data['author'][5:])), data['message_id'], data['log_message_body'])


class ThreadParticipantKickAction(Action):
    def __init__(self, msg, time, thread, author, mid, body, removed_participants):
        Action.__init__(self, msg)
        self.time, self.thread, self.removed_participants, self.author, self.mid, self.body = time, thread, removed_participants, author, mid, body

    @classmethod
    def from_pull(cls, msg, data):
        return cls(msg, datetime.fromtimestamp(data['timestamp'] / 1000.0), msg.get_thread(int(data['thread_fbid'])), msg.get_person(int(data['author'][5:])), data['message_id'], data['log_message_body'], [msg.get_person(int(p[5:])) for p in data['log_message_data']['removed_participants']])


class ThreadParticipantAddAction(Action):
    def __init__(self, msg, time, thread, author, mid, body, added_participants):
        Action.__init__(self, msg)
        self.time, self.thread, self.added_participants, self.author, self.mid, self.body = time, thread, added_participants, author, mid, body

    @classmethod
    def from_pull(cls, msg, data):
        return cls(msg, datetime.fromtimestamp(data['timestamp'] / 1000.0), msg.get_thread(int(data['thread_fbid'])), msg.get_person(int(data['author'][5:])), data['message_id'], data['log_message_body'], [msg.get_person(int(p[5:])) for p in data['log_message_data']['added_participants']])


class ThreadParticipantNameChangeAction(Action):
    def __init__(self, msg, time, thread, author, mid, body, participant, name):
        Action.__init__(self, msg)
        self.time, self.thread, self.author, self.mid, self.body, self.participant, self.name = time, thread, author, mid, body, participant, name

    @classmethod
    def from_pull(cls, msg, data):
        return cls(msg, datetime.fromtimestamp(data['timestamp'] / 1000.0), msg.get_thread(int(data['thread_fbid'])), msg.get_person(int(data['author'][5:])), data['message_id'], data['log_message_body'], msg.get_person(int(data['log_message_data']['untypedData']['participant_id'])), data['log_message_data']['untypedData']['nickname'])


class ThreadRenameAction(Action):
    def __init__(self, msg, time, thread, author, mid, body, name):
        Action.__init__(self, msg)
        self.time, self.thread, self.author, self.mid, self.body, self.name = time, thread, author, mid, body, name

    @classmethod
    def from_pull(cls, msg, data):
        return cls(msg, datetime.fromtimestamp(data['timestamp'] / 1000.0), msg.get_thread(int(data['thread_fbid'])), msg.get_person(int(data['author'][5:])), data['message_id'], data['log_message_body'], data['log_message_data']['name'])


class ThreadImageChangeAction(Action):
    def __init__(self, msg, time, thread, author, mid, body, image):
        Action.__init__(self, msg)
        self.time, self.thread, self.author, self.mid, self.body, self.image = time, thread, author, mid, body, image

    @classmethod
    def from_pull(cls, msg, data):
        return cls(msg, datetime.fromtimestamp(data['timestamp'] / 1000.0), msg.get_thread(int(data['thread_fbid'])), msg.get_person(int(data['author'][5:])), data['message_id'], data['log_message_body'], Attachment.from_dict(data['log_message_data']['image']))


class ThreadThemeColorChangeAction(Action):
    def __init__(self, msg, time, thread, author, mid, body, color):
        Action.__init__(self, msg)
        self.time, self.thread, self.author, self.mid, self.body, self.color = time, thread, author, mid, body, color

    @classmethod
    def from_pull(cls, msg, data):
        return cls(msg, datetime.fromtimestamp(data['timestamp'] / 1000.0), msg.get_thread(int(data['thread_fbid'])), msg.get_person(int(data['author'][5:])), data['message_id'], data['log_message_body'], data['log_message_data']['untypedData']['theme_color'])


class DeliveryAction(Action):
    def __init__(self, msg, time, thread):
        Action.__init__(self, msg)
        self.time, self.thread = time, thread

    @classmethod
    def from_pull(cls, msg, data):
        return cls(msg, datetime.fromtimestamp(data['timestamp'] / 1000.0), msg.get_thread(data['thread_fbid']))


class ReadAction(Action):
    def __init__(self, msg, time, thread, reader):
        Action.__init__(self, msg)
        self.time, self.thread, self.reader = time, thread, reader

    @classmethod
    def from_pull(cls, msg, data):
        return cls(msg, datetime.fromtimestamp(data['time'] / 1000.0), msg.get_thread(data['thread_fbid'] if 'thread_fbid' in data else data['reader']), msg.get_person(data['reader']))


class TypingAction(Action):
    def __init__(self, msg, thread, person, typing):
        Action.__init__(self, msg)
        self.thread, self.person, self.typing = thread, person, typing

    @classmethod
    def from_pull(cls, msg, data):
        return cls(msg, msg.get_thread(data['thread_fbid'] if 'thread_fbid' in data else data['from']), msg.get_person(data['from']), bool(data['st']))
