from __future__ import unicode_literals

import argparse
import time
import logging
import random
import string

from MessengerAPI.Messenger import Messenger
from MessengerAPI.Message import Message


__author__ = 'JuniorJPDJ'

logging.basicConfig(level=logging.DEBUG)


# thx stackoverflow
def randomword(length):
    return ''.join(random.choice(string.ascii_letters) for i in range(length))


p = argparse.ArgumentParser()
p.add_argument('email', help="E-Mail/Phone number/Other facebook login")
p.add_argument('password', help="Facebook password")
p.add_argument('thread', type=int, help="Messenger/Facebook thread id to test on")
p.add_argument('person', type=int, help="Messenger/Facebook person id to test on")

args = p.parse_args()


logging.info('Logging in')
msg = Messenger(args.email, args.password)
logging.info('Logged in')

logging.info('Getting thread {}'.format(args.thread))
thread = msg.get_thread(args.thread)
logging.info('Thread name: {}'.format(thread.get_name()))

name = thread.get_name()
newname = randomword(15)
logging.info('Changing name to {}'.format(newname))
thread.rename(newname)
logging.info('Setting it back')
thread.rename(name)

# logging.info('Sending random message')
# thread.send_message(randomword(64))

logging.info('Making messages read')
thread.make_read()

logging.info('Setting type status to true')
thread.send_typing()
logging.info('Sleeping for 10 seconds')
time.sleep(10)
logging.info('Setting type status to false')
thread.send_typing(False)

logging.info('Getting person')
person = msg.get_person(args.person)

logging.info('Adding person to thread')
thread.add_people([person])

name = randomword(8)
logging.info('Setting person\'s name to {}'.format(name))
thread.set_participant_name(person, name)

logging.info('Kicking person from thread')
thread.kick_person(person)

logging.info('Thread color: {}'.format(thread.custom_color))
color = hex(random.randint(0, 0xffffff))[2:]
color = '0' * (6 - len(color)) + color
logging.info('Setting color to {}'.format(color))
thread.set_custom_color(color)

logging.info('Loading participants')
for p in thread.participants:
    logging.info('{}: {}'.format(p.name, thread.get_participant_name(p)))

logging.info('Loading 30 messages from history')
for m in thread.load_older_messages():
    if isinstance(m, Message):
        logging.info(m.body)
    else:
        logging.info(type(m))
