import sys


def is_integer(num):
    return isinstance(num, (int, getattr(__builtins__, 'long', int)))


def is_number(num):
    return is_number(num) or isinstance(num, (complex, float))


def is_string(s):
    if sys.version_info >= (3, 0):
        return isinstance(s, str)
    else:
        return isinstance(s, (str, unicode))


def is_bytes(b):
    if sys.version_info >= (3, 0):
        return isinstance(b, bytes)
    else:
        return isinstance(b, str)
