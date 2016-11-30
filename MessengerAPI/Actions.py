from .Message import Message
from .Attachments import Attachment
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
                # now in delta
                # return Message.from_pull(msg, data['message'])
                return None
            elif data['event'] == 'delivery_receipt' and data['delivered'] == True:
                # now in delta
                # return DeliveryAction.from_pull(msg, data)
                return None
            elif data['event'] == 'read_receipt':
                # now in delta
                # return ReadAction.from_pull(msg, data)
                return None
            elif data['event'] == 'read':
                # the same as delta MarkRead
                return None
            elif data['event'] == 'change_mute_settings':
                # the same as ThreadMuteSettings
                return None
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
        elif data['type'] == 'delta':
            deltaclass = data['delta']['class']
            if deltaclass == 'NoOp':
                # does nothing?
                pass
            elif deltaclass == 'NewMessage':
                return Message.from_pull_delta(msg, data['delta'])
            elif deltaclass == 'MarkRead':
                return MakeReadAction.from_pull_delta(msg, data['delta'])
            elif deltaclass == 'ReadReceipt':
                return ReadAction.from_pull_delta(msg, data['delta'])
            elif deltaclass == 'DeliveryReceipt':
                return DeliveryAction.from_pull_delta(msg, data['delta'])
            elif deltaclass == 'ThreadMuteSettings':
                return SetMuteAction.from_pull_delta(msg, data['delta'])
            else:
                return cls.unknown(msg, data)
        elif data['type'] == 'buddylist_overlay':
            return BuddyListOverlayAction.from_pull(msg, data)
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
        return f

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

    @classmethod
    def from_pull_delta(cls, msg, data):
        return cls(msg, datetime.fromtimestamp(int(data['deliveredWatermarkTimestampMs']) / 1000.0), msg.get_thread(int(data['threadKey']['otherUserFbId' if 'otherUserFbId' in data['threadKey'] else 'threadFbId'])))


class ReadAction(Action):
    def __init__(self, msg, time, thread, reader):
        Action.__init__(self, msg)
        self.time, self.thread, self.reader = time, thread, reader

    @classmethod
    def from_pull(cls, msg, data):
        return cls(msg, datetime.fromtimestamp(data['time'] / 1000.0), msg.get_thread(int(data['thread_fbid'] if 'thread_fbid' in data else data['reader'])), msg.get_person(int(data['reader'])))

    @classmethod
    def from_pull_delta(cls, msg, data):
        thread = msg.get_thread(int(data['threadKey']['otherUserFbId' if 'otherUserFbId' in data['threadKey'] else 'threadFbId']))
        reader = msg.get_person(int(data['actorFbId'] if 'actorFbId' in data else data['threadKey']['otherUserFbId']))
        return cls(msg, datetime.fromtimestamp(int(data['actionTimestampMs']) / 1000.0), thread, reader)


class TypingAction(Action):
    def __init__(self, msg, thread, person, typing):
        Action.__init__(self, msg)
        self.thread, self.person, self.typing = thread, person, typing

    @classmethod
    def from_pull(cls, msg, data):
        return cls(msg, msg.get_thread(data['thread_fbid'] if 'thread_fbid' in data else data['from']), msg.get_person(data['from']), bool(data['st']))


class MakeReadAction(Action):
    def __init__(self, msg, time, thread):
        Action.__init__(self, msg)
        self.time, self.thread = time, thread

    @classmethod
    def from_pull_delta(cls, msg, data):
        thread = msg.get_thread(int(data['threadKeys'][0]['otherUserFbId' if 'otherUserFbId' in data['threadKeys'][0] else 'threadFbId']))
        return cls(msg, datetime.fromtimestamp(int(data['actionTimestamp']) / 1000.0), thread)


class SetMuteAction(Action):
    def __init__(self, msg, thread, mute):
        Action.__init__(self, msg)
        self.thread, self.mute = thread, mute

    @classmethod
    def from_pull_delta(cls, msg, data):
        thread = msg.get_thread(int(data['threadKey']['otherUserFbId' if 'otherUserFbId' in data['threadKey'] else 'threadFbId']))
        mute = int(data['expireTime'])
        mute = False if mute == 0 else True if mute == -1 else datetime.fromtimestamp(mute)
        return cls(msg, thread, mute)


class BuddyListOverlayAction(Action):
    def __init__(self, msg, person, last_active, p, ol, s, vc, a):
        Action.__init__(self, msg)
        self.person, self.last_active, self.p, self.ol, self.s, self.vc, self.a = person, last_active, p, ol, a, vc, a

    @classmethod
    def from_pull(cls, msg, data):
        r = []
        for o in data['overlay'].items():
            r.append(cls(msg, msg.get_person(int(o[0])), datetime.fromtimestamp(o[1]['la']), o[1]['p'] if 'p' in o[1] else None, o[1]['ol'] if 'ol' in o[1] else None, o[1]['s'] if 's' in o[1] else None, o[1]['vc'] if 'vc' in o[1] else None, o[1]['a'] if 'a' in o[1] else None))
        return tuple(r)
