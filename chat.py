__author__ = 'juniorjpdj'

import sys, time, getpass
from collections import deque
from MessengerAPI import Messenger

if sys.platform == "win32":
    encoding = sys.stdout.encoding
else:
    encoding = "utf8"


def safe_print(msg):
    print(unicode(msg).encode(encoding))

shown = deque(maxlen=30)


print('Logowanie')
email = raw_input('E-mail: ')
pw = getpass.getpass()
messenger = Messenger(email, pw)
print('Zalogowano')

friends = messenger.get_friends()
messenger.send_reconnect()
lastpull = 0

while 1:
    pulldelta = time.time() - lastpull
    if pulldelta < 3:
        time.sleep(pulldelta + 0.1)
    data = messenger.send_pull()
    lastpull = time.time()
    if data:
        for i in data:
            if i['type'] == 'messaging' and i['event'] == 'deliver':
                m = i['message']
                if m['mid'] not in shown:
                    shown.append(m['mid'])
                    sender = m['sender_name']
                    if str(m['sender_fbid']) == messenger.uid:
                        sender = 'Ja'
                    if 'group_thread_info' in m and m['group_thread_info']:
                        safe_print(u'{} -> Grupa: "{}": {}'.format(sender, m['group_thread_info']['name'], unicode(m['body'])))
                    else:
                        user = unicode(m['other_user_fbid'])
                        if user == messenger.uid or user == unicode(m['sender_fbid']):
                            user = 'Ja'
                        elif user in friends:
                            user = friends[user]['name']
                        safe_print(u'{} -> {}: {}'.format(sender, user, m['body']))