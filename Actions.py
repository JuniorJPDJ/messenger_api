from Message import Message
from Attachments import Attachment
from datetime import datetime

__author__ = 'JuniorJPDJ'

# TODO: buddylist_overlay action


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
                return cls.unknown(msg, data)
        elif data['type'] in ('ttyp', 'typ'):
            return TypingAction.from_pull(msg, data)
        elif data['type'] == 'mercury':
            out = []
            for a in data['actions']:
                if a['action_type'] == 'ma-type:log-message':
                    out.append(LogMessageAction.from_pull(msg, a))
                else:
                    out.append(Action.unknown(msg, a))
            return tuple(out)
        else:
            return cls.unknown(msg, data)


class LogMessageAction(Action):
    def __init__(self, msg, time, thread, author, mid, body):
        Action.__init__(self, msg)
        self.time, self.thread, self.author, self.mid, self.body = time, thread, author, mid, body

    @classmethod
    def unknown(cls, msg, data):
        f = cls(msg, datetime.fromtimestamp(data['timestamp'] / 1000.0), msg.get_thread(int(data['thread_fbid'])), msg.get_person(int(data['author'][5:])), data['message_id'], data['log_message_body'])
        f.data = data
        return data

    @classmethod
    def from_pull(cls, msg, data):
        if data['log_message_type'] == 'log:subscribe':
            return ThreadParticipantAddAction.from_pull(msg, data)
        elif data['log_message_type'] == 'log:unsubscribe':
            if len(data['log_message_data']['removed_participants']) == 1 and data['log_message_data']['removed_participants'][0] == data['author']:
                return ThreadParticipantLeaveAction.from_pull(msg, data)
            else:
                return ThreadParticipantKickAction.from_pull(msg, data)
        elif data['log_message_type'] == 'log:thread-name':
            return ThreadRenameAction.from_pull(msg, data)
        elif data['log_message_type'] == 'log:thread-image':
            return ThreadImageChangeAction.from_pull(msg, data)
        elif data['log_message_type'] == 'log:generic-admin-text':
            if data['log_message_data']['message_type'] == 'change_thread_theme':
                return ThreadThemeColorChangeAction.from_pull(msg, data)
            elif data['log_message_data']['message_type'] == 'change_thread_nickname':
                return ThreadParticipantNicknameChangeAction.from_pull(msg, data)
            elif data['log_message_data']['message_type'] == 'change_thread_icon':
                return ThreadEmoticonChangeAction.from_pull(msg, data)
            else:
                return cls.unknown(msg, data)
        else:
            return cls.unknown(msg, data)

    @classmethod
    def from_thread_info(cls, thread, data):
        if data['action_type'] == 'ma-type:user-generated-message':
            return Message.from_thread_info(thread, data)
        elif data['action_type'] == 'ma-type:log-message':
            return cls.from_pull(thread.messenger, data)
        else:
            return Action.unknown(thread.messenger, data)


class ThreadParticipantLeaveAction(LogMessageAction):
    @classmethod
    def from_pull(cls, msg, data):
        return cls(msg, datetime.fromtimestamp(data['timestamp'] / 1000.0), msg.get_thread(int(data['thread_fbid'])), msg.get_person(int(data['author'][5:])), data['message_id'], data['log_message_body'])


class ThreadParticipantKickAction(LogMessageAction):
    def __init__(self, msg, time, thread, author, mid, body, removed_participants):
        LogMessageAction.__init__(self, msg, time, thread, author, mid, body)
        self.removed_participants = removed_participants

    @classmethod
    def from_pull(cls, msg, data):
        return cls(msg, datetime.fromtimestamp(data['timestamp'] / 1000.0), msg.get_thread(int(data['thread_fbid'])), msg.get_person(int(data['author'][5:])), data['message_id'], data['log_message_body'], [msg.get_person(int(p[5:])) for p in data['log_message_data']['removed_participants']])


class ThreadParticipantAddAction(LogMessageAction):
    def __init__(self, msg, time, thread, author, mid, body, added_participants):
        LogMessageAction.__init__(self, msg, time, thread, author, mid, body)
        self.added_participants = added_participants

    @classmethod
    def from_pull(cls, msg, data):
        return cls(msg, datetime.fromtimestamp(data['timestamp'] / 1000.0), msg.get_thread(int(data['thread_fbid'])), msg.get_person(int(data['author'][5:])), data['message_id'], data['log_message_body'], [msg.get_person(int(p[5:])) for p in data['log_message_data']['added_participants']])


class ThreadParticipantNicknameChangeAction(LogMessageAction):
    def __init__(self, msg, time, thread, author, mid, body, participant, name):
        LogMessageAction.__init__(self, msg, time, thread, author, mid, body)
        self.participant, self.name = participant, name

    @classmethod
    def from_pull(cls, msg, data):
        return cls(msg, datetime.fromtimestamp(data['timestamp'] / 1000.0), msg.get_thread(int(data['thread_fbid'])), msg.get_person(int(data['author'][5:])), data['message_id'], data['log_message_body'], msg.get_person(int(data['log_message_data']['untypedData']['participant_id'])), data['log_message_data']['untypedData']['nickname'])


class ThreadRenameAction(LogMessageAction):
    def __init__(self, msg, time, thread, author, mid, body, name):
        LogMessageAction.__init__(self, msg, time, thread, author, mid, body)
        self.name = name

    @classmethod
    def from_pull(cls, msg, data):
        return cls(msg, datetime.fromtimestamp(data['timestamp'] / 1000.0), msg.get_thread(int(data['thread_fbid'])), msg.get_person(int(data['author'][5:])), data['message_id'], data['log_message_body'], data['log_message_data']['name'])


class ThreadImageChangeAction(LogMessageAction):
    def __init__(self, msg, time, thread, author, mid, body, image):
        LogMessageAction.__init__(self, msg, time, thread, author, mid, body)
        self.image = image

    @classmethod
    def from_pull(cls, msg, data):
        return cls(msg, datetime.fromtimestamp(data['timestamp'] / 1000.0), msg.get_thread(int(data['thread_fbid'])), msg.get_person(int(data['author'][5:])), data['message_id'], data['log_message_body'], Attachment.from_dict(data['log_message_data']['image']))


class ThreadEmoticonChangeAction(LogMessageAction):
    def __init__(self, msg, time, thread, author, mid, body, emoticon):
        LogMessageAction.__init__(self, msg, time, thread, author, mid, body)
        self.emoticon = emoticon

    @classmethod
    def from_pull(cls, msg, data):
        return cls(msg, datetime.fromtimestamp(data['timestamp'] / 1000.0), msg.get_thread(int(data['thread_fbid'])), msg.get_person(int(data['author'][5:])), data['message_id'], data['log_message_body'], data['log_message_data']['untypedData']['thread_icon'])


class ThreadThemeColorChangeAction(LogMessageAction):
    def __init__(self, msg, time, thread, author, mid, body, color):
        LogMessageAction.__init__(self, msg, time, thread, author, mid, body)
        self.color = color

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
