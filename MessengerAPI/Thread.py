from __future__ import unicode_literals

import datetime

from .Attachments import SendableAttachment, PhotoAttachment, UploadedAttachment
from .Message import Message
from .Actions import MercuryAction
from .Person import Person
from .utils.universal_type_checking import is_integer, is_string

__author__ = 'JuniorJPDJ'


class Thread(object):
    group = False

    def __init__(self, messenger, fbid, can_reply, archived, folder, custom_color, custom_nicknames, custom_emoji,
                 message_count, unread_count, last_msg_time, last_read_time, mute):
        assert is_integer(fbid)
        assert isinstance(can_reply, bool)
        assert isinstance(archived, bool)
        assert is_string(folder)
        assert is_string(custom_color) or custom_color is None
        assert isinstance(custom_nicknames, dict)
        assert is_string(custom_emoji) or custom_emoji is None
        assert is_integer(message_count)
        assert is_integer(unread_count)
        assert isinstance(last_msg_time, datetime.datetime)
        assert isinstance(last_read_time, (datetime.datetime, type(None)))
        assert isinstance(mute, (datetime.datetime, bool))
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
        assert is_string(body)
        if isinstance(attachment, SendableAttachment):
            attachment = attachment.to_dict()
        elif isinstance(attachment, dict):
            pass
        else:
            attachment = {}
        msg = Message.from_sending_dict(self.messenger.msgapi.send_msg(self.fbid, body, attachment, self.group), self, body)
        self.messages.append(msg)
        return msg

    def make_read(self):
        self.messenger.msgapi.send_read_status(self.fbid)
        self.unread_count = 0

    def send_typing(self, typing=True):
        assert isinstance(typing, bool)
        self.messenger.msgapi.send_typing(self.fbid, typing, self.group)

    def load_older_messages(self, amount=30):
        assert is_integer(amount)
        data = self.messenger.msgapi.get_thread_messages(self.fbid, amount, len(self.messages), self.group)
        msgs = MercuryAction.from_pull(self.messenger, data)
        self.messages = list(msgs) + self.messages
        return msgs

    def get_name(self):
        pass

    def get_participant_name(self, person):
        assert isinstance(person, Person)
        if person in self.custom_nicknames:
            return self.custom_nicknames[person]
        else:
            return person.name

    def rename(self, name):
        pass

    def set_participant_name(self, person, name):
        assert isinstance(person, Person)
        assert is_string(name)
        self.messenger.msgapi.change_custom_nickname(self.fbid, person.fbid, name)
        if name:
            self.custom_nicknames[person] = name
        elif person in self.custom_nicknames:
            del self.custom_nicknames[person]

    def set_custom_emoji(self, emoji):
        assert is_string(emoji)
        self.messenger.msgapi.change_custom_emoji(self.fbid, emoji)
        self.custom_emoji = emoji

    def set_custom_color(self, color):
        assert is_string(color)
        self.messenger.msgapi.change_custom_color(self.fbid, color)
        self.custom_color = color

    def set_mute(self, mute):
        assert isinstance(mute, (bool, datetime.datetime, datetime.timedelta)) or is_integer(mute)
        if isinstance(mute, bool):
            if mute:
                mutetime = -1
            else:
                mutetime = 0
        elif is_integer(mute):
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

    def get_image(self):
        raise NotImplementedError()


class PrivateThread(Thread):
    @classmethod
    def from_dict(cls, messenger, data):
        mute = int(data['mute_until']) if data['mute_until'] else 0
        mute = False if mute == 0 else True if mute == -1 else datetime.datetime.fromtimestamp(mute)

        custom_nicknames = dict([(messenger.get_person(int(fbid[0])), fbid[1]) for fbid in data['custom_nickname'].items()]) if data['custom_nickname'] is not None else dict()

        last_msg_time = None if data['last_message_timestamp'] == -1 else datetime.datetime.fromtimestamp(data['last_message_timestamp'] / 1000.0)
        last_read_time = None if data['last_read_timestamp'] == -1000 else datetime.datetime.fromtimestamp(data['last_read_timestamp'] / 1000.0)

        emoji = data['custom_like_icon']['emoji'] if data['custom_like_icon'] is not None and 'emoji' in data['custom_like_icon'] else None

        return cls(messenger, int(data['thread_fbid']), data['can_reply'], data['is_archived'], data['folder'],
                   data['custom_color'], custom_nicknames, emoji, data['message_count'],
                   data['unread_count'], last_msg_time, last_read_time, mute)

    def get_name(self):
        return self.get_participant_name(self.messenger.get_person(self.fbid))

    def rename(self, name):
        assert is_string(name)
        self.set_participant_name(self.messenger.get_person(self.fbid), name)

    def get_image(self):
        return self.messenger.get_person(self.fbid).image


class GroupThread(Thread):
    group = True

    def __init__(self, messenger, fbid, can_reply, archived, folder, custom_color, custom_nicknames, custom_emoji,
                 message_count, unread_count, last_msg_time, last_read_time, mute, participants, name, image):

        Thread.__init__(self, messenger, fbid, can_reply, archived, folder, custom_color, custom_nicknames, custom_emoji,
                        message_count, unread_count, last_msg_time, last_read_time, mute)
        assert isinstance(participants, list)
        assert is_string(name)
        assert is_string(image) or image is None
        self.participants, self.name, self.image = participants,  name, image

    @classmethod
    def from_dict(cls, messenger, data):
        mute = int(data['mute_until']) if data['mute_until'] else 0
        mute = False if mute == 0 else True if mute == -1 else datetime.datetime.fromtimestamp(mute)

        participants = [messenger.get_person(int(fbid[5:])) for fbid in data['participants']]

        custom_nicknames = dict([(messenger.get_person(int(fbid[0])), fbid[1]) for fbid in data['custom_nickname'].items()]) if data['custom_nickname'] is not None else dict()

        last_msg_time = None if data['last_message_timestamp'] == -1 else datetime.datetime.fromtimestamp(data['last_message_timestamp'] / 1000.0)
        last_read_time = None if data['last_read_timestamp'] in (-1000, -1) else datetime.datetime.fromtimestamp(data['last_read_timestamp'] / 1000.0)

        emoji = data['custom_like_icon']['emoji'] if data['custom_like_icon'] is not None and 'emoji' in data['custom_like_icon'] else None

        return cls(messenger, int(data['thread_fbid']), data['can_reply'], data['is_archived'], data['folder'],
                   data['custom_color'], custom_nicknames, emoji, data['message_count'],
                   data['unread_count'], last_msg_time, last_read_time, mute, participants, data['name'], data['image_src'])

    def leave(self):
        self.messenger.msgapi.leave_thread(self.fbid)
        self.participants.remove(self.messenger.me)

    def add_people(self, people):
        assert isinstance(people, list)
        self.messenger.msgapi.add_to_thread(self.fbid, [person.fbid for person in people])
        self.participants.extend(people)

    def kick_person(self, person):
        assert isinstance(person, Person)
        self.messenger.msgapi.kick_from_thread(self.fbid, person.fbid)
        self.participants.remove(person)

    def rename(self, name):
        assert is_string(name)
        self.messenger.msgapi.rename_thread(self.fbid, name)
        self.name = name

    def change_image(self, image_attachment):
        assert isinstance(image_attachment, PhotoAttachment) or (isinstance(image_attachment, UploadedAttachment) and image_attachment.typename == "image")
        self.messenger.msgapi.change_thread_image(self.fbid, image_attachment.fbid)
        self.image = image_attachment.url

    def get_image(self):
        return self.image

    def get_name(self, generate_if_none=True):
        assert isinstance(generate_if_none, bool)
        if self.name:
            return self.name
        elif generate_if_none:
            t = ', '.join([self.get_participant_name(p) for p in self.participants[:5]])
            t += ' and {} more...'.format(len(self.participants) - 5) if len(self.participants) > 5 else ''
            return t
