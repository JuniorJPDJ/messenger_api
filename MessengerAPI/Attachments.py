import sys

if sys.version_info >= (3, 0):
    unicode = str  # python3 support
    import urllib.parse as urlparse
else:
    import urlparse

__author__ = 'JuniorJPDJ'

# TODO: make attachment objects easy to send with message


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
class PhotoAttachment(Attachment):
    def __init__(self, data, fbid, size, preview_url, preview_size, large_preview_url, large_preview_size):
        Attachment.__init__(self, data, large_preview_url)
        self.fbid, self.size = fbid, size
        self.preview_url, self.preview_size = preview_url, preview_size
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


class VideoAttachment(Attachment):
    def __init__(self, data, url, fbid, width, height, duration):
        Attachment.__init__(self, data, url)
        self.fbid, self.height, self.width, self.duration = fbid, height, width, duration

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


class StickerAttachment(Attachment):
    def __init__(self, data, url, stickerid, packid):
        Attachment.__init__(self, data, url)
        self.stickerid, self.packid = stickerid, packid

    def __str__(self):
        return u'<StickerAttachment with stickerID = "{}">'.format(self.stickerid)

    def __repr__(self):
        return u'StickerAttachment(url={}, stickerid={}, packid={})'.format(self.url, self.stickerid, self.packid)

    @classmethod
    def from_dict(cls, data):
        return cls(data, unicode(data['url']), int(data['metadata']['stickerID']), int(data['metadata']['packID']))

Attachment.register_attach_type('sticker', StickerAttachment.from_dict)


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
