from MessengerAPI.Messenger import Messenger
from MessengerAPI.Message import Message
import time
import getpass
import logging
import sys
import random
import string


__author__ = 'JuniorJPDJ'

logging.basicConfig(level=logging.DEBUG)


# thx stackoverflow
def randomword(length):
    return ''.join(random.choice(string.ascii_letters) for i in range(length))

if len(sys.argv) > 0:
    email = sys.argv[1]
    logging.info('Using {} as email/login'.format(email))
    if len(sys.argv) > 1:
        pw = sys.argv[2]
        logging.info('Using password provided through parameter')
        if len(sys.argv) > 2:
            thread = sys.argv[3]
            logging.info('Using {} as test thread id'.format(thread))
            if len(sys.argv) > 3:
                person = sys.argv[4]
                logging.info('Using {} as test person id'.format(person))
            else:
                person = input('Test person id: ')
        else:
            thread = input('Test thread id: ')
            person = input('Test person id: ')
    else:
        pw = getpass.getpass()
        thread = input('Test thread id: ')
else:
    email = input('E-mail: ')
    pw = getpass.getpass()
    thread = input('Test thread id: ')

logging.info('Logging in')
msg = Messenger(email, pw)
logging.info('Logged in')

logging.info('Getting thread {}'.format(thread))
thread = msg.get_thread(thread)
logging.info('Thread name: {}'.format(thread.get_name()))

name = thread.get_name()
newname = randomword(15)
logging.info('Changing name to {}'.format(newname))
thread.rename(newname)
logging.info('Setting it back')
thread.rename(name)

logging.info('Sending random message')
thread.send_message(randomword(64))

logging.info('Making messages read')
thread.make_read()

logging.info('Setting type status to true')
thread.send_typing()
logging.info('Sleeping for 10 seconds')
time.sleep(10)
logging.info('Setting type status to false')
thread.send_typing(False)

logging.info('Loading 30 messages from history')
for m in thread.load_older_messages():
    if isinstance(m, Message):
        logging.info(m.body)
    else:
        logging.info(type(m))

logging.info('Loading participants')
for p in thread.participants:
    logging.info('{}: {}'.format(p.name, thread.get_participant_name(p)))

logging.info('Getting person')
person = msg.get_person(person)

logging.info('Adding person to thread')
thread.add_people([person])

logging.info('Kicking person from thread')
thread.kick_person(person)