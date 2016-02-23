from datetime import datetime
from Attachments import Attachment

__author__ = 'JuniorJPDJ'


class Message(object):
    def __init__(self, thread, author, mid, time, body, attachments=()):
        self.id, self.time, self.body, self.attachments = mid, time, body, attachments
        self.thread, self.author, self.delivered = thread, author, False

    @classmethod
    def from_pull(cls, messenger, data):
        thread = messenger.get_thread(int(data['thread_fbid'])) if 'thread_fbid' in data else messenger.get_thread(data['other_user_fbid'])
        return cls(thread, messenger.get_person(data['sender_fbid']), data['mid'], datetime.fromtimestamp(data['timestamp'] / 1000.0), data['body'], [Attachment.from_dict(a) for a in data['attachments']])

    @classmethod
    def from_thread_info(cls, thread, data):
        return cls(thread, thread.messenger.get_person(int(data['author'][5:])), data['message_id'], datetime.fromtimestamp(data['timestamp'] / 1000.0), data['body'], [Attachment.from_dict(a) for a in data['attachments']])

    @classmethod
    def from_sending_dict(cls, data, thread, body):
        data = data['actions'][0]
        return cls(thread, thread.messenger.me, data['message_id'], datetime.fromtimestamp(data['timestamp'] / 1000.0), body, [Attachment.from_dict(a) for a in data['attachments']])

    def send_deliviery_receipt(self):
        if not self.delivered and not self.sender == self.thread.messenger.me:
            self.thread.messenger.msgapi.send_delivery_receipt(self.id, self.thread.fbid)
