import sys

if sys.version_info >= (3, 0):
    unicode = str  # python3 support
    import urllib.parse as urlparse
else:
    import urlparse

__author__ = 'JuniorJPDJ'

# TODO: make attachment objects easy to send with message


class Attachment(object):
    def __init__(self, url):
        self.url = url

    @classmethod
    def from_dict(cls, data):
        if data['attach_type'] == 'file':
            if data['metadata'] and data['metadata']['type'] == 'fb_voice_message':
                return VoiceAttachment(unicode(data['url']), int(data['metadata']['duration']))
            else:
                return FileAttachment(unicode(data['url']), unicode(data['name']))
        elif data['attach_type'] == 'photo':
            d = data['metadata']['dimensions'].split(',')
            return PhotoAttachment(unicode(data['hires_url']), int(data['metadata']['fbid']), int(d[0]), int(d[1]))
        elif data['attach_type'] == 'animated_image':
            d = data['metadata']['dimensions'].split(',')
            return AnimatedImageAttachment(unicode(data['url']), int(data['metadata']['fbid']), int(d[0]), int(d[1]))
        elif data['attach_type'] == 'video':
            return VideoAttachment(unicode(data['url']), int(data['metadata']['fbid']), int(data['metadata']['dimensions']['height']), int(data['metadata']['dimensions']['width']), int(data['metadata']['duration']))
        elif data['attach_type'] == 'sticker':
            return StickerAttachment(unicode(data['url']), int(data['metadata']['stickerID']), int(data['metadata']['packID']))
        elif data['attach_type'] == 'share':
            if not data['share']['uri']:
                url = None
            elif 'l.facebook' in data['share']['uri']:
                url = unicode(urlparse.parse_qs(data['share']['uri'].split('?')[1])['u'][0])
            else:
                url = data['share']['uri']
            return ShareAttachment(url, unicode(data['share']['title']))
        else:
            return cls(data['url'])


class FileAttachment(Attachment):
    def __init__(self, url, name):
        Attachment.__init__(self, url)
        self.name = name

    def __str__(self):
        return u'<FileAttachment with name "{}">'.format(self.name)

    def __repr__(self):
        return u'FileAttachment(url={}, name={})'.format(self.url, self.name)


class VoiceAttachment(Attachment):
    def __init__(self, url, duration):
        Attachment.__init__(self, url)
        self.duration = duration

    def __str__(self):
        return u'<VoiceAttachment with {} seconds duration>'.format(self.duration / 1000.0)

    def __repr__(self):
        return u'VoiceAttachment(url={}, duration={})'.format(self.url, self.duration)


class PhotoAttachment(Attachment):
    def __init__(self, url, fbid, width, height):
        Attachment.__init__(self, url)
        self.fbid, self.height, self.width = fbid, height, width

    def __str__(self):
        return u'<PhotoAttachment ({}x{})>'.format(self.width, self.height)

    def __repr__(self):
        return u'PhotoAttachment(url={}, fbid={}, width={}, height={})'.format(self.url, self.fbid, self.width, self.height)


class AnimatedImageAttachment(Attachment):
    def __init__(self, url, fbid, width, height):
        Attachment.__init__(self, url)
        self.fbid, self.height, self.width = fbid, height, width

    def __str__(self):
        return u'<AnimatedImageAttachment ({}x{})>'.format(self.width, self.height)

    def __repr__(self):
        return u'AnimatedImageAttachment(url={}, fbid={}, width={}, height={})'.format(self.url, self.fbid, self.width, self.height)


class VideoAttachment(Attachment):
    def __init__(self, url, fbid, width, height, duration):
        Attachment.__init__(self, url)
        self.fbid, self.height, self.width, self.duration = fbid, height, width, duration

    def __str__(self):
        return u'<VideoAttachment ({}x{}) with {} seconds duration>'.format(self.width, self.height, self.duration)

    def __repr__(self):
        return u'VideoAttachment(url={}, fbid={}, width={}, height={}, duration={})'.format(self.url, self.fbid, self.width, self.height, self.duration)


class StickerAttachment(Attachment):
    def __init__(self, url, stickerid, packid):
        Attachment.__init__(self, url)
        self.stickerid, self.packid = stickerid, packid

    def __str__(self):
        return u'<StickerAttachment with stickerID = "{}">'.format(self.stickerid)

    def __repr__(self):
        return u'StickerAttachment(url={}, stickerid={}, packid={})'.format(self.url, self.stickerid, self.packid)


class ShareAttachment(Attachment):
    def __init__(self, url, name):
        Attachment.__init__(self, url)
        self.name = name

    def __str__(self):
        return u'<ShareAttachment with url = "{}">'.format(self.url)

    def __repr__(self):
        return u'ShareAttachment(url={}, name={})'.format(self.url, self.name)
