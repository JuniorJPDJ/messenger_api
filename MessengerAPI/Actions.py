from .Message import Message
from .Attachments import Attachment
from datetime import datetime

__author__ = 'JuniorJPDJ'


class Action(object):
    __type_handlers = {}

    @classmethod
    def register_type(cls, _type, handler):
        cls.__type_handlers[_type] = handler

    def __init__(self, msg, data):
        self.msg, self.data = msg, data

    @classmethod
    def from_pull(cls, msg, data):
        if data['type'] in cls.__type_handlers:
            return cls.__type_handlers[data['type']](msg, data)
        else:
            return cls(msg, data)


class MessagingAction(Action):
    __event_handlers = {}

    @classmethod
    def register_event(cls, event, handler):
        cls.__event_handlers[event] = handler

    @classmethod
    def from_pull(cls, msg, data):
        if data['event'] in cls.__event_handlers:
            return cls.__event_handlers[data['event']](msg, data)
        else:
            return cls(msg, data)

Action.register_type('messaging', MessagingAction.from_pull)

# now in delta
for _event in ['deliver', 'delivery_receipt', 'read_receipt', 'read', 'change_mute_settings']:
    MessagingAction.register_event(_event, lambda msg, data: None)


class TypingAction(Action):
    def __init__(self, msg, data, thread, person, typing):
        Action.__init__(self, msg, data)
        self.thread, self.person, self.typing = thread, person, typing

    @classmethod
    def from_pull(cls, msg, data):
        return cls(msg, data, msg.get_thread(data['thread_fbid'] if 'thread_fbid' in data else data['from']),
                   msg.get_person(data['from']), bool(data['st']))

Action.register_type('typ', TypingAction.from_pull)
Action.register_type('ttyp', TypingAction.from_pull)


class MercuryAction(Action):
    __action_type_handlers = {}

    @classmethod
    def register_action_type(cls, action_type, handler):
        cls.__action_type_handlers[action_type] = handler

    @classmethod
    def from_pull(cls, msg, data):
        out = []
        for a in data['actions']:
            if a['action_type'] in cls.__action_type_handlers:
                out.append(cls.__action_type_handlers[a['action_type']](msg, a))
            else:
                out.append(cls(msg, data))
        return tuple(out)

Action.register_type('mercury', MercuryAction.from_pull)
MercuryAction.register_action_type('ma-type:user-generated-message', Message.from_mercury_action)


class LogMessageAction(MercuryAction):
    __log_message_type_handlers = {}

    @classmethod
    def register_log_message_type(cls, log_message_type, handler):
        cls.__log_message_type_handlers[log_message_type] = handler

    def __init__(self, msg, data, time, thread, author, mid, body):
        Action.__init__(self, msg, data)
        self.time, self.thread, self.author, self.mid, self.body = time, thread, author, mid, body

    @classmethod
    def unknown(cls, msg, data):
        return cls(msg, data, datetime.fromtimestamp(data['timestamp'] / 1000.0), msg.get_thread(int(data['thread_fbid'])),
                   msg.get_person(int(data['author'][5:])), data['message_id'], data['log_message_body'])

    @classmethod
    def from_pull(cls, msg, data):
        if data['log_message_type'] in cls.__log_message_type_handlers:
            return cls.__log_message_type_handlers[data['log_message_type']](msg, data)
        else:
            return cls.unknown(msg, data)

MercuryAction.register_action_type('ma-type:log-message', LogMessageAction.from_pull)


class GenericAdminTextAction(LogMessageAction):
    __message_type_handlers = {}

    @classmethod
    def register_message_type(cls, message_type, handler):
        cls.__message_type_handlers[message_type] = handler

    @classmethod
    def from_pull(cls, msg, data):
        if data['log_message_data']['message_type'] in cls.__message_type_handlers:
            return cls.__message_type_handlers[data['log_message_data']['message_type']](msg, data)
        else:
            return cls.unknown(msg, data)

LogMessageAction.register_log_message_type('log:generic-admin-text', GenericAdminTextAction.from_pull)


class ThreadParticipantLeaveAction(LogMessageAction):
    @classmethod
    def from_pull(cls, msg, data):
        return cls(msg, data, datetime.fromtimestamp(data['timestamp'] / 1000.0), msg.get_thread(int(data['thread_fbid'])),
                   msg.get_person(int(data['author'][5:])), data['message_id'], data['log_message_body'])


class ThreadParticipantKickAction(LogMessageAction):
    def __init__(self, msg, data, time, thread, author, mid, body, removed_participants):
        LogMessageAction.__init__(self, msg, data, time, thread, author, mid, body)
        self.removed_participants = removed_participants

    @classmethod
    def from_pull(cls, msg, data):
        if len(data['log_message_data']['removed_participants']) == 1 and\
           data['log_message_data']['removed_participants'][0] == data['author']:
            return ThreadParticipantLeaveAction.from_pull(msg, data)
        else:
            return cls(msg, data, datetime.fromtimestamp(data['timestamp'] / 1000.0), msg.get_thread(int(data['thread_fbid'])),
                       msg.get_person(int(data['author'][5:])), data['message_id'], data['log_message_body'],
                       [msg.get_person(int(p[5:])) for p in data['log_message_data']['removed_participants']])

LogMessageAction.register_log_message_type('log:unsubscribe', ThreadParticipantKickAction.from_pull)


class ThreadParticipantAddAction(LogMessageAction):
    def __init__(self, msg, data, time, thread, author, mid, body, added_participants):
        LogMessageAction.__init__(self, msg, data, time, thread, author, mid, body)
        self.added_participants = added_participants

    @classmethod
    def from_pull(cls, msg, data):
        return cls(msg, data, datetime.fromtimestamp(data['timestamp'] / 1000.0), msg.get_thread(int(data['thread_fbid'])),
                   msg.get_person(int(data['author'][5:])), data['message_id'], data['log_message_body'],
                   [msg.get_person(int(p[5:])) for p in data['log_message_data']['added_participants']])

LogMessageAction.register_log_message_type('log:subscribe', ThreadParticipantAddAction.from_pull)


class ThreadRenameAction(LogMessageAction):
    def __init__(self, msg, data, time, thread, author, mid, body, name):
        LogMessageAction.__init__(self, msg, data, time, thread, author, mid, body)
        self.name = name

    @classmethod
    def from_pull(cls, msg, data):
        return cls(msg, data, datetime.fromtimestamp(data['timestamp'] / 1000.0), msg.get_thread(int(data['thread_fbid'])),
                   msg.get_person(int(data['author'][5:])), data['message_id'], data['log_message_body'],
                   data['log_message_data']['name'])

LogMessageAction.register_log_message_type('log:thread-name', ThreadRenameAction.from_pull)


class ThreadImageChangeAction(LogMessageAction):
    def __init__(self, msg, data, time, thread, author, mid, body, image):
        LogMessageAction.__init__(self, msg, data, time, thread, author, mid, body)
        self.image = image

    @classmethod
    def from_pull(cls, msg, data):
        return cls(msg, data, datetime.fromtimestamp(data['timestamp'] / 1000.0), msg.get_thread(int(data['thread_fbid'])),
                   msg.get_person(int(data['author'][5:])), data['message_id'], data['log_message_body'],
                   Attachment.from_dict(data['log_message_data']['image']))

LogMessageAction.register_log_message_type('log:thread-image', ThreadImageChangeAction.from_pull)


class ThreadParticipantNicknameChangeAction(GenericAdminTextAction):
    def __init__(self, msg, data, time, thread, author, mid, body, participant, name):
        GenericAdminTextAction.__init__(self, msg, data, time, thread, author, mid, body)
        self.participant, self.name = participant, name

    @classmethod
    def from_pull(cls, msg, data):
        return cls(msg, data, datetime.fromtimestamp(data['timestamp'] / 1000.0), msg.get_thread(int(data['thread_fbid'])),
                   msg.get_person(int(data['author'][5:])), data['message_id'], data['log_message_body'],
                   msg.get_person(int(data['log_message_data']['untypedData']['participant_id'])),
                   data['log_message_data']['untypedData']['nickname'])

GenericAdminTextAction.register_message_type('change_thread_nickname', ThreadParticipantNicknameChangeAction.from_pull)


class ThreadEmoticonChangeAction(GenericAdminTextAction):
    def __init__(self, msg, data, time, thread, author, mid, body, emoticon):
        GenericAdminTextAction.__init__(self, msg, data, time, thread, author, mid, body)
        self.emoticon = emoticon

    @classmethod
    def from_pull(cls, msg, data):
        return cls(msg, data, datetime.fromtimestamp(data['timestamp'] / 1000.0), msg.get_thread(int(data['thread_fbid'])),
                   msg.get_person(int(data['author'][5:])), data['message_id'], data['log_message_body'],
                   data['log_message_data']['untypedData']['thread_icon'])

GenericAdminTextAction.register_message_type('change_thread_icon', ThreadEmoticonChangeAction.from_pull)


class ThreadThemeColorChangeAction(GenericAdminTextAction):
    def __init__(self, msg, data, time, thread, author, mid, body, color):
        GenericAdminTextAction.__init__(self, msg, data, time, thread, author, mid, body)
        self.color = color

    @classmethod
    def from_pull(cls, msg, data):
        return cls(msg, data, datetime.fromtimestamp(data['timestamp'] / 1000.0), msg.get_thread(int(data['thread_fbid'])),
                   msg.get_person(int(data['author'][5:])), data['message_id'], data['log_message_body'],
                   data['log_message_data']['untypedData']['theme_color'])

GenericAdminTextAction.register_message_type('change_thread_theme', ThreadThemeColorChangeAction.from_pull)


class DeltaAction(Action):
    __delta_class_handlers = {}

    @classmethod
    def register_delta_class(cls, delta_class, handler):
        cls.__delta_class_handlers[delta_class] = handler

    @classmethod
    def from_pull(cls, msg, data):
        if data['delta']['class'] in cls.__delta_class_handlers:
            return cls.__delta_class_handlers[data['delta']['class']](msg, data['delta'])
        else:
            return cls(msg, data['delta'])

Action.register_type('delta', DeltaAction.from_pull)
DeltaAction.register_delta_class('NewMessage', Message.from_pull)


class DeliveryAction(DeltaAction):
    def __init__(self, msg, data, time, thread):
        DeltaAction.__init__(self, msg, data)
        self.time, self.thread = time, thread

    @classmethod
    def from_pull(cls, msg, data):
        return cls(msg, data, datetime.fromtimestamp(int(data['deliveredWatermarkTimestampMs']) / 1000.0),
                   msg.get_thread(int(data['threadKey']['otherUserFbId' if 'otherUserFbId' in data['threadKey'] else 'threadFbId'])))

DeltaAction.register_delta_class('DeliveryReceipt', DeliveryAction.from_pull)


class ReadAction(DeltaAction):
    def __init__(self, msg, data, time, thread, reader):
        DeltaAction.__init__(self, msg, data)
        self.time, self.thread, self.reader = time, thread, reader

    @classmethod
    def from_pull(cls, msg, data):
        thread = msg.get_thread(int(data['threadKey']['otherUserFbId' if 'otherUserFbId' in data['threadKey'] else 'threadFbId']))
        reader = msg.get_person(int(data['actorFbId'] if 'actorFbId' in data else data['threadKey']['otherUserFbId']))
        return cls(msg, data, datetime.fromtimestamp(int(data['actionTimestampMs']) / 1000.0), thread, reader)

DeltaAction.register_delta_class('ReadReceipt', ReadAction.from_pull)


class MakeReadAction(DeltaAction):
    def __init__(self, msg, data, time, thread):
        DeltaAction.__init__(self, msg, data)
        self.time, self.thread = time, thread

    @classmethod
    def from_pull(cls, msg, data):
        thread = msg.get_thread(int(data['threadKeys'][0]['otherUserFbId' if 'otherUserFbId' in data['threadKeys'][0] else 'threadFbId']))
        return cls(msg, data, datetime.fromtimestamp(int(data['actionTimestamp']) / 1000.0), thread)

DeltaAction.register_delta_class('MarkRead', MakeReadAction.from_pull)


class SetMuteAction(DeltaAction):
    def __init__(self, msg, data, thread, mute):
        DeltaAction.__init__(self, msg, data)
        self.thread, self.mute = thread, mute

    @classmethod
    def from_pull(cls, msg, data):
        thread = msg.get_thread(int(data['threadKey']['otherUserFbId' if 'otherUserFbId' in data['threadKey'] else 'threadFbId']))
        mute = int(data['expireTime'])
        mute = False if mute == 0 else True if mute == -1 else datetime.fromtimestamp(mute)
        return cls(msg, data, thread, mute)

DeltaAction.register_delta_class('ThreadMuteSettings', SetMuteAction.from_pull)


class BuddyListOverlayAction(Action):
    def __init__(self, msg, data, person, last_active, p, ol, s, vc, a):
        Action.__init__(self, msg, data)
        self.person, self.last_active, self.p, self.ol, self.s, self.vc, self.a = person, last_active, p, ol, s, vc, a

    @classmethod
    def from_pull(cls, msg, data):
        r = []
        for o in data['overlay'].items():
            r.append(cls(msg, o, msg.get_person(int(o[0])), datetime.fromtimestamp(o[1]['la']), o[1].get('p', None),
                         o[1].get('ol', None), o[1].get('s', None), o[1].get('vc', None), o[1].get('p', None)))
        return tuple(r)

Action.register_type('buddylist_overlay', BuddyListOverlayAction.from_pull)
