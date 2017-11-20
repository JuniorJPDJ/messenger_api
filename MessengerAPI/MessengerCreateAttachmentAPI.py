from __future__ import unicode_literals

import json
import mimetypes
import os

from .base.MessengerAPI import str_base, MessengerAPI
from .Messenger import Messenger

__author__ = 'JuniorJPDJ'

# TODO: merge with Attachments.py (partially done)


class MessengerCreateAttachment(object):
    def __init__(self, messenger):
        assert isinstance(messenger, (MessengerAPI, Messenger))

        if isinstance(messenger, Messenger):
            self.messenger = messenger.msgapi
        else:
            self.messenger = messenger

    def attach_url(self, link):
        resp = self.messenger.send_req('/message_share_attachment/fromURI/', 1,
                                       {'fb_dtsg': self.messenger.dtsg_token, 'ttstamp': self.messenger.ttstamp,
                                        'disallow_delayed': True, 'image_width': 920, 'image_height': 920, 'uri': link})

        def makedata(data, prefix):
            out = {}
            if type(data) == list:
                j = 0
                for i in data:
                    data[j] = (j, i)
                    j += 1
                data = dict(data)
            for i in data.items():
                if type(i[1]) in (dict, list):
                    out.update(makedata(i[1], '{}[{}]'.format(prefix, i[0])))
                elif type(i[1]) == list:
                    for j in i[1]:
                        out.update(makedata(j, '{}[{}]'.format(prefix, i[0])))
                else:
                    out['{}[{}]'.format(prefix, i[0])] = i[1]

            return out

        return makedata(json.loads(resp.text[9:])['payload']['share_data'], 'shareable_attachment')

    def attach_file(self, filename):
        self.messenger.uploadid += 1
        self.messenger.reqid += 1
        resp = self.messenger.sess.post('https://upload.messenger.com/ajax/mercury/upload.php',
                              params={'__user': self.messenger.uid, '__a': 1, '__req': str_base(self.messenger.reqid),
                                      '__rev': self.messenger.rev, 'fb_dtsg': self.messenger.dtsg_token,
                                      'ttstamp': self.messenger.ttstamp}, data={'images_only': 'false'},
                              files={'upload_{}'.format(self.messenger.uploadid):
                                     (os.path.basename(filename), open(filename, 'rb'),
                                      mimetypes.guess_type(filename)[0] or 'application/octet-stream')})

        data = json.loads(resp.text[9:])['payload']['metadata'][0]

        attachment = {'has_attachment': 'true',
                      'preview_attachments[0][upload_id]': 'upload_{}'.format(self.messenger.uploadid),
                      'preview_attachments[0][attach_type]': 'photo',
                      'preview_attachments[0][preview_uploading]': 'true',
                      'upload_id': 'upload_{}'.format(self.messenger.uploadid)}

        if 'image_id' in data:
            attachment.update({'image_ids[0]': data['image_id']})
        elif 'file_id' in data:
            attachment.update({'file_ids[0]': data['file_id']})

        return attachment

    @staticmethod
    def attach_sticker(stickerid):
        return {'body': '',
                'sticker_id': stickerid}
