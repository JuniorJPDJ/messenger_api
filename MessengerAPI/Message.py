from __future__ import unicode_literals

from datetime import datetime

from .Attachments import Attachment
from .Actions import LogMessageAction, DeltaAction

__author__ = 'JuniorJPDJ'


class Message(LogMessageAction):
    def __init__(self, data, thread, author, mid, time, body, attachments=()):
        LogMessageAction.__init__(self, thread.messenger, data, time, thread, author, mid, body)
        assert isinstance(attachments, tuple)
        self.delivered, self.id, self.attachments = False, mid, attachments

    @classmethod
    def from_pull(cls, msg, data):
        thread = msg.get_thread(int(data['messageMetadata']['threadKey']['otherUserFbId' if 'otherUserFbId' in data['messageMetadata']['threadKey'] else 'threadFbId']))
        attachments = []
        if 'attachments' in data:
            for a in data['attachments']:
                attachments.append(Attachment.from_dict(a['mercury']))

        return cls(data, thread, msg.get_person(int(data['messageMetadata']['actorFbId'])), data['messageMetadata']['messageId'],
                   datetime.fromtimestamp(int(data['messageMetadata']['timestamp']) / 1000.0),
                   data['body'] if 'body' in data else '', tuple(attachments))

    @classmethod
    def from_mercury_action(cls, msg, data):
        return cls(data, msg.get_thread(int(data['thread_fbid'])), msg.get_person(int(data['author'][5:])), data['message_id'],
                   datetime.fromtimestamp(data['timestamp'] / 1000.0), data['body'],
                   tuple([Attachment.from_dict(a) for a in data['attachments']]))

    @classmethod
    def from_sending_dict(cls, data, thread, body):
        data = data['actions'][0]
        return cls(data, thread, thread.messenger.me, data['message_id'], datetime.fromtimestamp(data['timestamp'] / 1000.0),
                   body, tuple([Attachment.from_dict(a) for a in data['attachments']]))

    def send_deliviery_receipt(self):
        if not self.delivered and not self.author == self.thread.messenger.me:
            self.thread.messenger.msgapi.send_delivery_receipt(self.id, self.thread.fbid)

DeltaAction.register_delta_class('NewMessage', Message.from_pull)
