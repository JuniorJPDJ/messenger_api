from enum import Enum
from .base.Exceptions import UnknownDictFormatException

__author__ = 'JuniorJPDJ'


class Gender(Enum):
    fanpage = 0
    female = 1
    male = 2
    wtf = 7


class Person(object):
    def __init__(self, messenger, fbid, name, short_name, image, imgsmall, gender):
        assert isinstance(fbid, int)
        self.messenger = messenger
        self.fbid, self.name, self.short_name, self.image, self.imgsmal, self.gender = fbid, name, short_name, image, imgsmall, gender
        self.last_active = None

    @classmethod
    def from_dict(cls, messenger, data):
        if 'short_name' in data:
            return cls(messenger, int(data['fbid']), data['name'], data['short_name'], data['big_image_src'], False, Gender(data['gender']))
        elif 'firstName' in data:
            return cls(messenger, int(data['id']), data['name'], data['firstName'], data['thumbSrc'], True, Gender(data['gender']))
        else:
            raise UnknownDictFormatException

    def get_thread(self):
        return self.messenger.get_thread(self.fbid)