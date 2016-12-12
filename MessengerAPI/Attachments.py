from __future__ import unicode_literals

import mimetypes
import json
import sys

from .base.MessengerAPI import str_base

if sys.version_info >= (3, 0):
    unicode = str  # python3 support
    import urllib.parse as urlparse
else:
    import urlparse

__author__ = 'JuniorJPDJ'


class AttachmentUploader(object):
    def __init__(self, msg):
        """
        :type msg: Messenger
        """
        self.msg = msg

    def _upload(self, filename, filelike, mimetype=None):
        api = self.msg.msgapi
        api.uploadid += 1
        api.reqid += 1

        mimetype = mimetypes.guess_type(filename)[0] or 'application/octet-stream' if mimetype is None else mimetype

        params = {'__user': api.uid, '__a': 1, '__req': str_base(api.reqid), '__rev': api.rev,
                  'fb_dtsg': api.dtsg_token, 'ttstamp': api.ttstamp}
        data = {'images_only': 'false'}
        files = {'upload_{}'.format(api.uploadid): (filename, filelike, mimetype)}

        resp = api.sess.post('https://upload.messenger.com/ajax/mercury/upload.php', params=params, data=data, files=files)

        return json.loads(resp.text[9:])['payload']['metadata'][0]

    def upload(self, filename, filelike, mimetype=None):
        payload = self._upload(filename, filelike, mimetype)

        _type = None
        for i in payload:
            if i.endswith('_id'):
                _type = i
                break

        return UploadedAttachment(payload, payload['src'], _type, payload[_type])


class Attachment(object):
    __attach_type_handlers = {}

    @classmethod
    def register_attach_type(cls, attach_type, handler):
        cls.__attach_type_handlers[attach_type] = handler

    def __init__(self, data, url):
        self.data, self.url = data, url

    @classmethod
    def from_dict(cls, data):
        if data['attach_type'] in cls.__attach_type_handlers:
            return cls.__attach_type_handlers[data['attach_type']](data)
        else:
            return cls(data, data['url'])


class SendableAttachment(Attachment):
    """
    This class is interface for attachment, that can be sent with message (reuse or upload)
    """
    def to_dict(self):
        raise NotImplementedError('Override me!')


class MultiSendableAttachment(SendableAttachment):
    """
    This class makes interface for attachment, what can be sent more than one in one message
    """
    typename = 'override_me'

    def __init__(self, data, url, fbid):
        SendableAttachment.__init__(self, data, url)
        self.fbid = fbid

    def to_dict(self, num=0):
        return {'has_attachment': True, '{}_ids[{}]'.format(self.typename, num): self.fbid}


class MultiSendableAttachments(SendableAttachment):
    """
    This class is helping to send more than one MultiSendableAttachment with one message
    """
    def __init__(self, attachments_iterable):
        """
        :type attachments_iterable: iterable of MultiSendableAttachment
        """
        SendableAttachment.__init__(self, attachments_iterable, None)
        self._attachments = []
        for a in attachments_iterable:
            if isinstance(a, MultiSendableAttachment):
                self._attachments.append(a)

    def to_dict(self):
        r = {}
        for i in range(len(self._attachments)):
            r.update(self._attachments[i].to_dict(i))
        return r


class UploadedAttachment(MultiSendableAttachment):
    def __init__(self, data, url, typename, fbid):
        MultiSendableAttachment.__init__(self, data, url, fbid)
        self.typename = typename[:-3]


class FileAttachment(Attachment):
    def __init__(self, data, url, name):
        Attachment.__init__(self, data, url)
        self.name = name

    def __str__(self):
        return u'<FileAttachment with name "{}">'.format(self.name)

    def __repr__(self):
        return u'FileAttachment(url={}, name={})'.format(self.url, self.name)

    @classmethod
    def from_dict(cls, data):
        if data['metadata'] and data['metadata']['type'] == 'fb_voice_message':
            return VoiceAttachment(data, unicode(data['url']), int(data['metadata']['duration']))
        else:
            return cls(data, unicode(data['url']), unicode(data['name']))

Attachment.register_attach_type('file', FileAttachment.from_dict)


class VoiceAttachment(Attachment):
    def __init__(self, data, url, duration):
        Attachment.__init__(self, data, url)
        self.duration = duration

    def __str__(self):
        return u'<VoiceAttachment with {} seconds duration>'.format(self.duration / 1000.0)

    def __repr__(self):
        return u'VoiceAttachment(url={}, duration={})'.format(self.url, self.duration)


# TODO: get real photo url
class PhotoAttachment(MultiSendableAttachment):
    typename = "image"

    def __init__(self, data, fbid, size, preview_url, preview_size, large_preview_url, large_preview_size):
        MultiSendableAttachment.__init__(self, data, large_preview_url, fbid)
        self.size, self.preview_url, self.preview_size = size, preview_url, preview_size
        self.large_preview_url, self.large_preview_size = large_preview_url, large_preview_size

    def __str__(self):
        return u'<{}.{} ({}x{})>'.format(__name__, self.__class__.__name__, self.size[0], self.size[1])

    def __repr__(self):
        return (u'PhotoAttachment(fbid={}, size={}, preview_url={}, '
                u'preview_size={}, large_preview_url={}, large_preview_size={})'
                .format(self.fbid, self.size, self.preview_url, self.preview_size, self.large_preview_url,
                        self.large_preview_url))

    @classmethod
    def from_dict(cls, data):
        size = tuple([int(i) for i in data['metadata']['dimensions'].split(',')])
        preview_size = (data['preview_width'], data['preview_height'])
        large_preview_size = (data['large_preview_width'], data['large_preview_height'])
        return cls(data, int(data['metadata']['fbid']), size, data['preview_url'], preview_size, data['large_preview_url'],
                   large_preview_size)

Attachment.register_attach_type('photo', PhotoAttachment.from_dict)


class AnimatedImageAttachment(PhotoAttachment):
    pass

Attachment.register_attach_type('animated_image', AnimatedImageAttachment.from_dict)


class VideoAttachment(MultiSendableAttachment):
    typename = "video"

    def __init__(self, data, url, fbid, width, height, duration):
        MultiSendableAttachment.__init__(self, data, url, fbid)
        self.height, self.width, self.duration = height, width, duration

    def __str__(self):
        return u'<VideoAttachment ({}x{}) with {} seconds duration>'.format(self.width, self.height, self.duration)

    def __repr__(self):
        return u'VideoAttachment(url={}, fbid={}, width={}, height={}, duration={})'.format(self.url, self.fbid,
                                                                                            self.width, self.height,
                                                                                            self.duration)

    @classmethod
    def from_dict(cls, data):
        return cls(data, unicode(data['url']), int(data['metadata']['fbid']), int(data['metadata']['dimensions']['height']),
                   int(data['metadata']['dimensions']['width']), int(data['metadata']['duration']))

Attachment.register_attach_type('video', VideoAttachment.from_dict)


class StickerAttachment(SendableAttachment):
    def __init__(self, data, url, stickerid, packid):
        SendableAttachment.__init__(self, data, url)
        self.stickerid, self.packid = stickerid, packid

    def __str__(self):
        return u'<StickerAttachment with stickerID = "{}">'.format(self.stickerid)

    def __repr__(self):
        return u'StickerAttachment(url={}, stickerid={}, packid={})'.format(self.url, self.stickerid, self.packid)

    @classmethod
    def from_dict(cls, data):
        return cls(data, unicode(data['url']), int(data['metadata']['stickerID']), int(data['metadata']['packID']))

    @classmethod
    def create(cls, stickerid, packid=None):
        return cls(None, None, stickerid, packid)

    def to_dict(self):
        return {'has_attachment': True, 'sticker_id': self.stickerid}

Attachment.register_attach_type('sticker', StickerAttachment.from_dict)


# TODO: Creating and resending Shares
class ShareAttachment(Attachment):
    def __init__(self, data, url, name):
        Attachment.__init__(self, data, url)
        self.name = name

    def __str__(self):
        return u'<ShareAttachment with url = "{}">'.format(self.url)

    def __repr__(self):
        return u'ShareAttachment(url={}, name={})'.format(self.url, self.name)

    @classmethod
    def from_dict(cls, data):
        if not data['share']['uri']:
            url = None
        elif 'facebook.com/l.php' in data['share']['uri']:
            url = unicode(urlparse.parse_qs(data['share']['uri'].split('?')[1])['u'][0])
        else:
            url = data['share']['uri']
        return cls(data, url, unicode(data['share']['title']))

Attachment.register_attach_type('share', ShareAttachment.from_dict)
