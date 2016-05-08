import getpass
import logging
import sys
from MessengerAPI.base.MessengerAPI import MessengerAPI
from MessengerAPI.base.MessengerPullParserV1 import MessengerPullParser

if sys.version_info >= (3, 0):
    unicode = str  # python3 support
    raw_input = input

__author__ = 'JuniorJPDJ'

# This file is using legacy API and may not work as it should

if sys.platform == "win32":
    encoding = sys.stdout.encoding
else:
    encoding = "utf8"

logging.basicConfig(level=logging.DEBUG)


def safe_print(msg):
    print(unicode(msg).encode(encoding))


def show_msg(date, sender, recipient, body, attachments):
    safe_print(unicode(date.strftime('[%H:%M.%S]  {} -> {}:{}{}')).format(sender, recipient, u' \'{}\''.format(body) if body else u'', u' + {}'.format(attachments) if len(attachments) else u''))


# noinspection PyUnusedLocal
def group_msg_handler(datetime, sender, group, message_body, attachments):
    show_msg(datetime, sender[1], u'Group \'{}\''.format(group[1]), message_body, attachments)


# noinspection PyUnusedLocal
def msg_handler(datetime, sender, message_body, attachments):
    show_msg(datetime, sender[1], u'Me', message_body, attachments)


# noinspection PyUnusedLocal
def own_group_msg_handler(datetime, group, message_body, attachments):
    show_msg(datetime, u'Me', u'Group \'{}\''.format(group[1]), message_body, attachments)


# noinspection PyUnusedLocal
def own_msg_handler(datetime, recipient, message_body, attachments):
    show_msg(datetime, u'Me', recipient[1], message_body, attachments)


# noinspection PyUnusedLocal
def group_leave_handler(datetime, user, group):
    safe_print(unicode(datetime.strftime('[%H:%M.%S] {} left the group \'{}\'')).format(user[1], group[1]))


# noinspection PyUnusedLocal
def group_kick_handler(datetime, kicker, user, group):
    safe_print(unicode(datetime.strftime('[%H:%M.%S] {} has been kicked from the group \'{}\' by {}')).format(user[1], group[1], kicker[1]))


# noinspection PyUnusedLocal
def group_add_handler(datetime, adder, user, group):
    safe_print(unicode(datetime.strftime('[%H:%M.%S] {} has been added to the group \'{}\' by {}')).format(user[1], group[1], adder[1]))


# noinspection PyUnusedLocal
def group_rename_handler(datetime, performer_id, group_id, new_group_name):
    safe_print(unicode(datetime.strftime('[%H:%M.%S] {} changed group ({}) name to \'{}\'')).format(performer_id, group_id, new_group_name))


# noinspection PyUnusedLocal
def group_change_avatar_handler(datetime, performer_id, group_id, avatar):
    safe_print(unicode(datetime.strftime('[%H:%M.%S] {} changed group ({}) avatar to \'{}\'')).format(performer_id, group_id, avatar.url))


# noinspection PyUnusedLocal
def read_handler(datetime, reader):
    safe_print(unicode(datetime.strftime('[%H:%M.%S] {} read messages')).format(reader))


# noinspection PyUnusedLocal
def group_read_handler(datetime, group_id, reader):
    safe_print(unicode(datetime.strftime('[%H:%M.%S] {} read messages in group {}')).format(reader, group_id))


# noinspection PyUnusedLocal
def group_started_typing_handler(datetime, group_id, user_id):
    safe_print(unicode(datetime.strftime('[%H:%M.%S] {} started typing in group {}')).format(user_id, group_id))


# noinspection PyUnusedLocal
def group_stopped_typing_handler(datetime, group_id, user_id):
    safe_print(unicode(datetime.strftime('[%H:%M.%S] {} stopped typing in group {}')).format(user_id, group_id))


# noinspection PyUnusedLocal
def started_typing_handler(datetime, from_id):
    safe_print(unicode(datetime.strftime('[%H:%M.%S] {} started typing to you')).format(from_id))


# noinspection PyUnusedLocal
def stopped_typing_handler(datetime, from_id):
    safe_print(unicode(datetime.strftime('[%H:%M.%S] {} stopped typing to you')).format(from_id))


# noinspection PyUnusedLocal
def thread_color_theme_change_handler(datetime, thread_id, author_id, color):
    safe_print(unicode(datetime.strftime('[%H:%M.%S] {} changed color in thread {} to {}')).format(author_id, thread_id, color))


# noinspection PyUnusedLocal
def thread_participant_nickname_change_handler(datetime, thread_id, author_id, participant_id, nickname):
    safe_print(unicode(datetime.strftime('[%H:%M.%S] {} changed nickname of {} in thread {} to {}')).format(author_id, participant_id, thread_id, nickname))


print('Logging in')
if sys.argv[1] and sys.argv[2]:
    email, pw = sys.argv[1:3]
else:
    email = raw_input('E-mail: ')
    pw = getpass.getpass()
messenger = MessengerAPI(email, pw)
print('Logged in')

rtc = MessengerPullParser(messenger)

rtc.register_handler('group_msg', group_msg_handler)
rtc.register_handler('msg', msg_handler)
rtc.register_handler('own_group_msg', own_group_msg_handler)
rtc.register_handler('own_msg', own_msg_handler)
rtc.register_handler('group_leave', group_leave_handler)
rtc.register_handler('group_kick', group_kick_handler)
rtc.register_handler('group_add', group_add_handler)
rtc.register_handler('group_rename', group_rename_handler)
rtc.register_handler('group_change_avatar', group_change_avatar_handler)
rtc.register_handler('read', read_handler)
rtc.register_handler('group_read', group_read_handler)
rtc.register_handler('group_started_typing', group_started_typing_handler)
rtc.register_handler('group_stopped_typing', group_stopped_typing_handler)
rtc.register_handler('started_typing', started_typing_handler)
rtc.register_handler('stopped_typing', stopped_typing_handler)
rtc.register_handler('thread_color_theme_change', thread_color_theme_change_handler)
rtc.register_handler('thread_participant_nickname_change', thread_participant_nickname_change_handler)

while 1:
    rtc.make_pull()
