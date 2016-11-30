import datetime
from .Message import Message
from .Actions import LogMessageAction

__author__ = 'JuniorJPDJ'


class Thread(object):
    group = False

    def __init__(self, messenger, fbid, can_reply, archived, folder, custom_color, custom_nicknames, custom_emoji,
                 message_count, unread_count, last_msg_time, last_read_time, mute):
        assert isnumber(fbid)
        self.messenger = messenger
        self.fbid, self.can_reply, self.archived, self.folder = fbid, can_reply, archived, folder
        self.custom_color, self.custom_nicknames, self.custom_emoji = custom_color, custom_nicknames, custom_emoji
        self.message_count, self.unread_count, self.last_msg_time = message_count, unread_count, last_msg_time
        self.last_read_time, self.mute = last_read_time, mute
        self.messages = []
        self.last_delivery = None
        self.last_read = {}

    def __repr__(self):
        return u"<MessengerAPI.Thread.{}: \"{}\" ({})>".format(self.__class__.__name__, self.get_name(), self.fbid)

    @classmethod
    def from_dict(cls, messenger, data):
        if data['other_user_fbid'] is None:
            return GroupThread.from_dict(messenger, data)
        else:
            return PrivateThread.from_dict(messenger, data)

    def send_message(self, body='', attachment=None):
        if attachment is None:
            attachment = {}
        msg = Message.from_sending_dict(self.messenger.msgapi.send_msg(self.fbid, body, attachment, self.group), self, body)
        self.messages.append(msg)
        return msg

    def make_read(self):
        self.messenger.msgapi.send_read_status(self.fbid)
        self.unread_count = 0

    def send_typing(self, typing=True):
        self.messenger.msgapi.send_typing(self.fbid, typing, self.group)

    def load_older_messages(self, amount=30):
        data = self.messenger.msgapi.get_thread_messages(self.fbid, amount, len(self.messages), self.group)
        msgs = [LogMessageAction.from_thread_info(self, m) for m in (data['actions'] if 'actions' in data else [])]
        self.messages = msgs + self.messages
        return msgs

    def get_name(self):
        pass

    def get_participant_name(self, person):
        if person in self.custom_nicknames:
            return self.custom_nicknames[person]
        else:
            return person.name

    def rename(self, name):
        pass

    def set_participant_name(self, person, name):
        self.messenger.msgapi.change_custom_nickname(self.fbid, person.fbid, name)
        if name:
            self.custom_nicknames[person] = name
        elif person in self.custom_nicknames:
            del self.custom_nicknames[person]

    def set_custom_emoji(self, emoji):
        self.messenger.msgapi.change_custom_emoji(self.fbid, emoji)
        self.custom_emoji = emoji

    def set_custom_color(self, color):
        self.messenger.msgapi.change_custom_color(self.fbid, color)
        self.custom_color = color

    def set_mute(self, mute):
        assert isinstance(mute, (bool, datetime.datetime, datetime.timedelta, int, __builtins__.get('long')))
        if isinstance(mute, bool):
            if mute:
                mutetime = -1
            else:
                mutetime = 0
        elif isnumber(mute):
            mutetime = mute
        elif isinstance(mute, datetime.datetime):
            mute = datetime.datetime.now() - mute

        if isinstance(mute, datetime.timedelta):
            mutetime = int(mute.total_seconds())

        self.messenger.msgapi.set_mute_thread(self.fbid, mutetime if mutetime >= -1 else 0)
        self.mute = mute

    def is_muted(self):
        if isinstance(self.mute, bool):
            return self.mute
        else:
            return self.mute > datetime.datetime.now()


class PrivateThread(Thread):
    @classmethod
    def from_dict(cls, messenger, data):
        mute = int(data['mute_until']) if data['mute_until'] else 0
        mute = False if mute == 0 else True if mute == -1 else datetime.datetime.fromtimestamp(mute)

        custom_nicknames = dict([(messenger.get_person(int(fbid[0])), fbid[1]) for fbid in data['custom_nickname'].items()]) if data['custom_nickname'] is not None else dict()

        last_msg_time = None if data['last_message_timestamp'] == -1 else datetime.datetime.fromtimestamp(data['last_message_timestamp'] / 1000.0)
        last_read_time = None if data['last_read_timestamp'] == -1 else datetime.datetime.fromtimestamp(data['last_read_timestamp'] / 1000.0)

        return cls(messenger, int(data['thread_fbid']), data['can_reply'], data['is_archived'], data['folder'],
                   data['custom_color'], custom_nicknames, data['custom_like_icon'], data['message_count'],
                   data['unread_count'], last_msg_time, last_read_time, mute)

    def get_name(self):
        return self.get_participant_name(self.messenger.get_person(self.fbid))

    def rename(self, name):
        self.set_participant_name(self.messenger.get_person(self.fbid), name)


class GroupThread(Thread):
    group = True

    def __init__(self, messenger, fbid, can_reply, archived, folder, custom_color, custom_nicknames, custom_emoji,
                 message_count, unread_count, last_msg_time, last_read_time, mute, participants, name, image):

        Thread.__init__(self, messenger, fbid, can_reply, archived, folder, custom_color, custom_nicknames, custom_emoji,
                        message_count, unread_count, last_msg_time, last_read_time, mute)
        self.participants, self.name, self.image = participants,  name, image

    @classmethod
    def from_dict(cls, messenger, data):
        mute = int(data['mute_until']) if data['mute_until'] else 0
        mute = False if mute == 0 else True if mute == -1 else datetime.datetime.fromtimestamp(mute)

        participants = [messenger.get_person(int(fbid[5:])) for fbid in data['participants']]

        custom_nicknames = dict([(messenger.get_person(int(fbid[0])), fbid[1]) for fbid in data['custom_nickname'].items()]) if data['custom_nickname'] is not None else dict()

        last_msg_time = None if data['last_message_timestamp'] == -1 else datetime.datetime.fromtimestamp(data['last_message_timestamp'] / 1000.0)
        last_read_time = None if data['last_read_timestamp'] == -1 else datetime.datetime.fromtimestamp(data['last_read_timestamp'] / 1000.0)

        return cls(messenger, int(data['thread_fbid']), data['can_reply'], data['is_archived'], data['folder'],
                   data['custom_color'], custom_nicknames, data['custom_like_icon'], data['message_count'],
                   data['unread_count'], last_msg_time, last_read_time, mute, participants, data['name'], data['image_src'])

    def leave(self):
        self.messenger.msgapi.leave_thread(self.fbid)

    def add_people(self, people):
        self.messenger.msgapi.add_to_thread(self.fbid, [person.fbid for person in people])

    def kick_person(self, person):
        self.messenger.msgapi.kick_from_thread(self.fbid, person.fbid)

    def rename(self, name):
        self.messenger.msgapi.rename_thread(self.fbid, name)

    def change_image(self, image):
        # TODO: implement changing image
        raise NotImplementedError

    def get_name(self):
        if self.name:
            return self.name
        else:
            t = ', '.join([self.get_participant_name(p) for p in self.participants[:5]])
            t += ' and {} more...'.format(len(self.participants) - 5) if len(self.participants) > 5 else ''
            return t


def isnumber(num):
    return isinstance(num, (int, __builtins__.get('long')))
