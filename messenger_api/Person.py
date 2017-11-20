from __future__ import unicode_literals

from enum import Enum

from .base.Exceptions import UnknownDictFormatException
from .utils.universal_type_checking import is_integer, is_string

__author__ = 'JuniorJPDJ'


class Gender(Enum):
    fanpage = 0
    female = 1
    male = 2
    # please, help, I don't know what's that..
    gender_3 = 3
    gender_4 = 4
    gender_5 = 5
    gender_6 = 6
    gender_7 = 7
    chatbot = 11  # GearBest has that "gender"


class Person(object):
    def __init__(self, messenger, fbid, name, short_name, image, imgsmall, gender):
        assert is_integer(fbid)
        assert is_string(name)
        assert is_string(short_name)
        assert is_string(image)
        assert isinstance(imgsmall, bool)
        assert isinstance(gender, Gender)
        self.messenger = messenger
        self.fbid, self.name, self.short_name = fbid, name, short_name
        self.image, self.imgsmall, self.gender = image, imgsmall, gender
        self.last_active = None

    def __repr__(self):
        return u"<messenger_api.Person.Person: \"{}\" ({})>".format(self.name, self.fbid)

    @classmethod
    def from_dict(cls, messenger, data):
        if 'short_name' in data:
            return cls(messenger, int(data['fbid']), data['name'], data['short_name'], data['big_image_src'],
                       False, Gender(data['gender']))
        elif 'firstName' in data:
            return cls(messenger, int(data['id']), data['name'], data['firstName'], data['thumbSrc'], True,
                       Gender(data['gender']))
        else:
            raise UnknownDictFormatException

    def get_thread(self):
        return self.messenger.get_thread(self.fbid)
