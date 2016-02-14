from datetime import datetime
from Message import Message

__author__ = 'JuniorJPDJ'


class Thread(object):
    group = False

    def __init__(self, messenger, fbid, can_reply, archived, folder, custom_color, custom_nickname, custom_like_icon, message_count, unread_count, last_msg_time, last_read_time):
        self.messenger = messenger
        self.fbid, self.can_reply, self.archived, self.folder = fbid, can_reply, archived, folder
        self.custom_color, self.custom_nickname, self.custom_like_icon = custom_color, custom_nickname, custom_like_icon
        self.message_count, self.unread_count, self.last_msg_time, self.last_read_time = message_count, unread_count, last_msg_time, last_read_time
        self.messages = []

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

    def send_typing(self, typing=True):
        self.messenger.msgapi.send_typing(self.fbid, typing, self.group)

    def load_older_messages(self, amount=30):
        # TODO: fix loading history, log messages should crash it
        data = self.messenger.msgapi.get_thread_messages(self.fbid, amount, len(self.messages), self.group)
        data = data['actions'] if 'actions' in data else []
        msgs = [Message.from_thread_info(self, m) for m in data]
        self.messages = msgs + self.messages
        return msgs


class PrivateThread(Thread):
    def __init__(self, messenger, fbid, can_reply, archived, folder, custom_color, custom_nickname, custom_like_icon, message_count, unread_count, last_msg_time, last_read_time):
        Thread.__init__(self, messenger, fbid, can_reply, archived, folder, custom_color, custom_nickname, custom_like_icon, message_count, unread_count, last_msg_time, last_read_time)

    @classmethod
    def from_dict(cls, messenger, data):
        return cls(messenger, int(data['thread_fbid']), data['can_reply'], data['is_archived'], data['folder'], data['custom_color'], data['custom_nickname'], data['custom_like_icon'], data['message_count'], data['unread_count'], datetime.fromtimestamp(data['last_message_timestamp'] / 1000.0), datetime.fromtimestamp(data['last_read_timestamp'] / 1000.0))


class GroupThread(Thread):
    group = True

    def __init__(self, messenger, fbid, can_reply, archived, folder, custom_color, custom_nickname, custom_like_icon, message_count, unread_count, last_msg_time, last_read_time, participants, former_participants, name, image):
        Thread.__init__(self, messenger, fbid, can_reply, archived, folder, custom_color, custom_nickname, custom_like_icon, message_count, unread_count, last_msg_time, last_read_time)
        self.participants, self.former_participants, self.name, self.image = participants, former_participants, name, image

    @classmethod
    def from_dict(cls, messenger, data):
        return cls(messenger, int(data['thread_fbid']), data['can_reply'], data['is_archived'], data['folder'], data['custom_color'], data['custom_nickname'], data['custom_like_icon'], data['message_count'], data['unread_count'], datetime.fromtimestamp(data['last_message_timestamp'] / 1000.0), datetime.fromtimestamp(data['last_read_timestamp'] / 1000.0), [messenger.get_person(int(fbid[5:])) for fbid in data['participants']], [int(fbid['id'][5:]) for fbid in data['former_participants']], data['name'], data['image_src'])

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
