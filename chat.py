__author__ = 'juniorjpdj'

import sys, getpass
from MessengerAPI import Messenger
from MessengerRealTimeChatAPI import MessengerRealTimeChat

if sys.platform == "win32":
    encoding = sys.stdout.encoding
else:
    encoding = "utf8"

def safe_print(msg):
    print(unicode(msg).encode(encoding))

def show_msg(date, sender, recipient, body, attachments):

    safe_print(unicode(date.strftime('[%H:%M.%S] {} -> {}:{}{}')).format(sender, recipient, u' "{}"'.format(body) if body else u'', u' + {}'.format(attachments) if len(attachments) else u''))

def group_msg_handler(datetime, (sender_id, sender_name), (group_id, group_name), message_body, attachments):
    show_msg(datetime, sender_name, u'Group "{}"'.format(group_name), message_body, attachments)

def msg_handler(datetime, (sender_id, sender_name), message_body, attachments):
    show_msg(datetime, sender_name, u'Me', message_body, attachments)

def own_group_msg_handler(datetime, (group_id, group_name), message_body, attachments):
    show_msg(datetime, u'Me', u'Group "{}"'.format(group_name), message_body, attachments)

def own_msg_handler(datetime, (recipient_id, recipient_name), message_body, attachments):
    show_msg(datetime, u'Me', recipient_name, message_body, attachments)

print('Logging in')
email = raw_input('E-mail: ')
pw = getpass.getpass()
messenger = Messenger(email, pw)
print('Logged in')

rtc = MessengerRealTimeChat(messenger)

rtc.register_group_msg_handler(group_msg_handler)
rtc.register_msg_handler(msg_handler)
rtc.register_own_group_msg_handler(own_group_msg_handler)
rtc.register_own_msg_handler(own_msg_handler)

while 1:
    rtc.make_pull()