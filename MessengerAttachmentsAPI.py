import urlparse, logging

__author__ = 'JuniorJPDJ'

# TODO: make attachment objects easy to send with message

class Attachment(object):
    def __new__(cls, a):
        if a['attach_type'] == 'file':
            if a['metadata'] and a['metadata']['type'] == 'fb_voice_message':
                return VoiceAttachment(unicode(a['url']), int(a['metadata']['duration']))
            else:
                return FileAttachment(unicode(a['url']), unicode(a['name']))
        elif a['attach_type'] == 'photo':
            d = a['metadata']['dimensions'].split(',')
            return PhotoAttachment(unicode(a['hires_url']), int(a['metadata']['fbid']), int(d[0]), int(d[1]))
        elif a['attach_type'] == 'animated_image':
            d = a['metadata']['dimensions'].split(',')
            return AnimatedImageAttachment(unicode(a['url']), int(a['metadata']['fbid']), int(d[0]), int(d[1]))
        elif a['attach_type'] == 'video':
            return VideoAttachment(unicode(a['url']), int(a['metadata']['fbid']), int(a['metadata']['dimensions']['height']), int(a['metadata']['dimensions']['width']), int(a['metadata']['duration']))
        elif a['attach_type'] == 'sticker':
            return StickerAttachment(unicode(a['url']), int(a['metadata']['stickerID']), int(a['metadata']['packID']))
        elif a['attach_type'] == 'share':
            # TODO: subattachment
            if not a['share']['uri']:
                url = None
            elif 'l.facebook' in a['share']['uri']:
                url = unicode(urlparse.parse_qs(a['share']['uri'].split('?')[1])['u'][0])
            else:
                url = a['share']['uri']
            return ShareAttachment(url, unicode(a['share']['title']))
        else:
            return object.__new__(cls, a['url'])

    def __init__(self, url):
        self.url = url


class FileAttachment(object):
    def __init__(self, url, name):
        self.url, self.name = url, name

    def __unicode__(self):
        return u'<FileAttachment with name "{}">'.format(self.name)

    def __repr__(self):
        return u'FileAttachment(url={}, name={})'.format(self.url, self.name)


class VoiceAttachment(object):
    def __init__(self, url, duration):
        self.url, self.duration = url, duration

    def __unicode__(self):
        return u'<VoiceAttachment with {} seconds duration>'.format(self.duration / 1000.0)

    def __repr__(self):
        return u'VoiceAttachment(url={}, duration={})'.format(self.url, self.duration)


class PhotoAttachment(object):
    def __init__(self, url, fbid, width, height):
        self.url, self.fbid, self.height, self.width = url, fbid, height, width

    def __unicode__(self):
        return u'<PhotoAttachment ({}x{})>'.format(self.width, self.height)

    def __repr__(self):
        return u'PhotoAttachment(url={}, fbid={}, width={}, height={})'.format(self.url, self.fbid, self.width, self.height)


class AnimatedImageAttachment(object):
    def __init__(self, url, fbid, width, height):
        self.url, self.fbid, self.height, self.width = url, fbid, height, width

    def __unicode__(self):
        return u'<AnimatedImageAttachment ({}x{})>'.format(self.width, self.height)

    def __repr__(self):
        return u'AnimatedImageAttachment(url={}, fbid={}, width={}, height={})'.format(self.url, self.fbid, self.width, self.height)


class VideoAttachment(object):
    def __init__(self, url, fbid, width, height, duration):
        self.url, self.fbid, self.height, self.width, self.duration = url, fbid, height, width, duration

    def __unicode__(self):
        return u'<VideoAttachment ({}x{}) with {} seconds duration>'.format(self.width, self.height, self.duration)

    def __repr__(self):
        return u'VideoAttachment(url={}, fbid={}, width={}, height={}, duration={})'.format(self.url, self.fbid, self.width, self.height, self.duration)


class StickerAttachment(object):
    def __init__(self, url, stickerid, packid):
        self.url, self.stickerid, self.packid = url, stickerid, packid

    def __unicode__(self):
        return u'<StickerAttachment with stickerID = "{}">'.format(self.stickerid)

    def __repr__(self):
        return u'StickerAttachment(url={}, stickerid={}, packid={})'.format(self.url, self.stickerid, self.packid)


class ShareAttachment(object):
    def __init__(self, url, name):
        self.url, self.name = url, name

    def __unicode__(self):
        return u'<ShareAttachment with url = "{}">'.format(self.url)

    def __repr__(self):
        return u'ShareAttachment(url={}, name={})'.format(self.url, self.name)
