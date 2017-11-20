from __future__ import unicode_literals

import json
import random
import requests
import time
import sys

from .Exceptions import *


if sys.version_info >= (3, 0):
    unicode = str  # python3 support

__author__ = 'JuniorJPDJ'
__version__ = 0.2

# Main features:
# DONE: login
# DONE: logout
# DONE: send message
# DONE: add users (list/tuple of users) to group thread
# DONE: kick participant from group thread
# DONE: leave group thread
# DONE: rename group thread
# DONE: send delivery receipt
# DONE: send read status
# DONE: send typing status
# DONE: get thread list
# DONE: get thread messages
# DONE: get thread info
# DONE: send pull request                                                   Used in MessengerPullParser
# DONE: get users info
# DONE: search
# DONE: change thread color theme
# DONE: change custom name of pariticipant of thread
# DONE: change thread image

# Additional features:
# NOPE: unread_threads                                                      There is no need to use it. I think filtering at thread list is doing this well
# NOPE: thread_sync                                                         I don't know what it really does, so at the moment I don't care about it
# DONE: parse mercury_payload, make some methods to make use of this        done at objective version


def str_base(num, b=36, numerals="0123456789abcdefghijklmnopqrstuvwxyz"):
    return ((num == 0) and numerals[0]) or (str_base(num // b, b, numerals).lstrip(numerals[0]) + numerals[num % b])


def check_for_messenger_error(req):
    if req.status_code != 200:
        raise MessengerException(req.status_code, 'HTTP Error', 'invalid request?')

    out = json.loads(req.text[9:])
    if 'error' in out:
        raise MessengerException(out['error'], out['errorSummary'], out['errorDescription'])


class MessengerAPI(object):
    def __init__(self, login, pw, useragent='default'):
        # login may also be email or phone number
        self.sess = requests.Session()

        debug_proxy = False
        if debug_proxy:
            self.sess.proxies.update({'https': 'https://127.0.0.1:8080'})
            self.sess.verify = False
            from requests.packages.urllib3.exceptions import InsecureRequestWarning
            requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
        self.sess.headers.update(
            {'User-agent': 'Mozilla/5.0 ;compatible; PyMessengerAPI/{}; KaziCiota; +http://juniorjpdj.cf;'.format(__version__) if useragent == 'default' else useragent})

        co = self.sess.get('https://www.messenger.com').text

        lsd_token = co.split('"token":"', 1)[1].split('"', 1)[0]
        initreqid = co.split('initialRequestID":"', 1)[1].split('"', 1)[0]
        timezone = (time.timezone if (time.localtime().tm_isdst == 0) else time.altzone) / 60
        lgnrnd = co.split('name="lgnrnd" value="', 1)[1].split('"', 1)[0]
        lgnjs = int(time.time())
        identifier = co.split('identifier":"', 1)[1].split('"', 1)[0]
        try:
            datr = co.split('"_js_datr","', 1)[1].split('"', 1)[0]
            self.sess.cookies.update({'_js_datr': datr})
        except IndexError:
            pass

        self.sess.get('https://www.facebook.com/login/messenger_dot_com_iframe/',
                      params={'redirect_uri': 'https://www.messenger.com/login/fb_iframe_target/?initial_request_id={}'
                              .format(initreqid), 'identifier': identifier, 'initial_request_id': initreqid})

        res = self.sess.post('https://www.messenger.com/login/password/',
                             {'lsd': lsd_token, 'initial_request_id': initreqid, 'timezone': timezone, 'lgnrnd': lgnrnd,
                              'lgnjs': lgnjs, 'email': login, 'pass': pw, 'default_persistent': 0}, headers={'Referer': 'https://www.messenger.com'})

        if res.url != "https://www.messenger.com/" or res.status_code != 200:
            raise LoggingInError

        data = res.text

        self.dtsg_token = data.split('"token":"', 1)[1].split('"', 1)[0]

        self.ttstamp = '2'
        for w in range(len(self.dtsg_token)):
            self.ttstamp += str(ord(self.dtsg_token[w]))

        self.reqid = 0
        self.uploadid = 1023
        self.sessid = str_base(random.randint(0, 2147483647), 16)

        self.rev = data.split('revision":', 1)[1].split(',', 1)[0]
        self.uid = data.split('USER_ID":"', 1)[1].split('"', 1)[0]

        # TODO: find a solution, that works always
        # self.locale = data.split('locale:"')[1].split('"')[0]
        # self.lang = data.split('language:"')[1].split('"')[0]
        # self.locale = data.split('locale:')[1].split('"')[0]
        # self.lang = data.split('language:')[1].split('"')[0]
        self.locale = data.split('locale":"', 1)[1].split('"', 1)[0]
        self.lang = data.split('language":"', 1)[1].split('"', 1)[0]


        self.last_active = json.loads(data.split('"lastActiveTimes":', 1)[1].split('},', 1)[0]+'}')

        o = u''
        t = 0
        for c in data.split('"mercuryPayload":', 1)[1]:
            if c == '{':
                t += 1
            elif c == "}":
                t -= 1
                if t == 0:
                    o += '}'
                    break
            o += c
        self.mercury_payload = json.loads(o)

        self.initdata = data

        self.partition, self.user_channel, self.pull_host, self.seq = (None, None, None, None)
        self.sticky_token, self.sticky_pool, self.tr = (None, None, None)

    def send_req(self, url, reqtype, data):
        defurl = 'https://www.messenger.com'
        defdata = {'__user': self.uid, '__a': 1, '__req': str_base(self.reqid), '__rev': self.rev}
        data.update(defdata)
        self.reqid += 1

        if reqtype:
            resp = self.sess.post(defurl + url, data, headers={'Referer': defurl})
        else:
            resp = self.sess.get(defurl + url, params=data, headers={'Referer': defurl})

        return resp

    def send_msg(self, thread_id, msg='', attachment=None, group=False, _id=None):
        # max length 20k chars, 10k unicoode chars
        if attachment is None:
            attachment = {}
        thread_id = unicode(thread_id)
        msg = unicode(msg)
        if _id is None:
            _id = random.randint(0, 999999999999999999)
        data = {'action_type': 'ma-type:user-generated-message',
                'author': 'fbid:' + self.uid,
                'source': 'source:messenger:web',
                'body': msg,
                'has_attachment': 'false',
                'html_body': 'false',
                'timestamp': int(time.time() * 1000),
                'offline_threading_id': _id,
                'message_id': _id,
                'client': 'mercury', 'fb_dtsg': self.dtsg_token, 'ttstamp': self.ttstamp}
        if group:
            userdata = {'thread_fbid': thread_id}
        else:
            userdata = {'specific_to_list[0]': 'fbid:' + thread_id,
                        'specific_to_list[1]': 'fbid:' + self.uid,
                        'other_user_fbid': thread_id}
        data.update(userdata)
        data.update(attachment)

        req = self.send_req('/messaging/send/', 1, data)

        check_for_messenger_error(req)

        return json.loads(req.text[9:])['payload']

    def send_log_message(self, thread_id, log_message_type, additional_data):
        _id = random.randint(0, 999999999999999999)
        data = {'action_type': 'ma-type:log-message',
                'author': 'fbid:' + self.uid,
                'source': 'source:messenger:web',
                'log_message_type': log_message_type,
                'thread_fbid': thread_id,
                'offline_threading_id': _id,
                'message_id': _id,
                'timestamp': int(time.time() * 1000),
                'client': 'messenger', 'fb_dtsg': self.dtsg_token, 'ttstamp': self.ttstamp}
        data.update(additional_data)

        req = self.send_req('/messaging/send/', 1, data)

        check_for_messenger_error(req)

        return req

    def send_messaging_request(self, _type, source, thread_id, additional_data):
        data = {'fb_dtsg': self.dtsg_token, 'ttstamp': self.ttstamp, 'thread_or_other_fbid': thread_id}
        data.update(additional_data)

        req = self.send_req('/messaging/{type}/?source={source}'.format(type=_type, source=source), 1, data)

        check_for_messenger_error(req)

        return req

    def change_custom_nickname(self, thread_id, user, nickname):
        data = {'participant_id': user, 'nickname': nickname}
        return self.send_messaging_request('save_thread_nickname', 'thread_settings', thread_id, data)

    def change_custom_color(self, thread_id, color):
        data = {'color_choice': color}
        return self.send_messaging_request('save_thread_color', 'thread_settings', thread_id, data)

    def change_custom_emoji(self, thread_id, emoji):
        data = {'emoji_choice': emoji}
        return self.send_messaging_request('save_thread_emoji', 'thread_settings', thread_id, data)

    def change_thread_image(self, thread_id, image_id):
        return self.send_log_message(thread_id, 'log:thread-image', {'log_message_data[image][image_id]': image_id})

    def add_to_thread(self, thread_id, users):
        return self.send_log_message(thread_id, 'log:subscribe',
                                     dict([['log_message_data[added_participants][{}]'.format(users.index(x)),
                                            'fbid:{}'.format(x)] for x in users]))

    def kick_from_thread(self, thread_id, user):
        data = {'fb_dtsg': self.dtsg_token, 'ttstamp': self.ttstamp}

        req = self.send_req('/chat/remove_participants/?uid={}&tid={}'.format(user, thread_id), 1, data)

        check_for_messenger_error(req)

        return req

    def leave_thread(self, thread_id):
        return self.kick_from_thread(thread_id, self.uid)

    def rename_thread(self, thread_id, name):
        return self.send_log_message(thread_id, 'log:thread-name', {'log_message_data[name]': name})

    def send_reconnect(self, reason=6):
        resp = self.send_req('/ajax/presence/reconnect.php', 0, {'reason': reason, 'fb_dtsg': self.dtsg_token})
        data = json.loads(resp.text[9:])
        self.partition = data['payload']['partition']
        self.user_channel = data['payload']['user_channel']
        self.pull_host = '{}-{}'.format(random.randint(0, 7), data['payload']['host'])
        self.seq = data['payload']['seq']

        return resp

    def send_delivery_receipt(self, msg_id, thread_id):
        data = {'message_ids[0]': msg_id, 'thread_ids[{}][0]'.format(thread_id): msg_id,
                'fb_dtsg': self.dtsg_token, 'ttstamp': self.ttstamp}

        req = self.send_req('/ajax/mercury/delivery_receipts.php', 1, data)
        check_for_messenger_error(req)
        return req

    def send_read_status(self, thread_id, timestamp=None):
        if timestamp is None:
            timestamp = int(time.time() * 1000)
        data = {'ids[{}]'.format(thread_id): True, 'watermarkTimestamp': timestamp, 'shouldSendReadReceipt': True,
                'fb_dtsg': self.dtsg_token, 'ttstamp': self.ttstamp}

        req = self.send_req('/ajax/mercury/change_read_status.php', 1, data)
        check_for_messenger_error(req)
        return req

    def send_typing(self, thread_id, typing=True, group=False):
        data = {'typ': int(typing), 'thread': thread_id, 'fb_dtsg': self.dtsg_token, 'ttstamp': self.ttstamp}
        if not group:
            data.update({'to': thread_id})
        req = self.send_req('/ajax/messaging/typ.php', 1, data)
        check_for_messenger_error(req)
        return req

    def get_thread_list(self, folder='inbox', limit=10, offset=0, _filter=None):
        assert folder in ('inbox', 'pending', 'other')
        assert _filter in (None, 'unread')
        data = {'{}[offset]'.format(folder): offset, '{}[limit]'.format(folder): limit,
                'fb_dtsg': self.dtsg_token, 'ttstamp': self.ttstamp}
        if _filter is not None:
            data.update({'{}[filter]'.format(folder): _filter})
        req = self.send_req('/ajax/mercury/threadlist_info.php', 1, data)
        check_for_messenger_error(req)
        return json.loads(req.text[9:])['payload']

    def get_thread_messages(self, thread, limit=20, offset=0, group=False):
        if group:
            f = 'thread_fbids'
        else:
            f = 'user_ids'
        data = {'messages[{}][{}][offset]'.format(f, thread): offset, 'messages[{}][{}][limit]'.format(f, thread): limit,
                'fb_dtsg': self.dtsg_token, 'ttstamp': self.ttstamp}
        req = self.send_req('/ajax/mercury/thread_info.php', 1, data)
        check_for_messenger_error(req)
        return json.loads(req.text[9:])['payload']

    def get_threads_info(self, group_threads=(), user_threads=()):
        data = {'fb_dtsg': self.dtsg_token, 'ttstamp': self.ttstamp}
        i = 0
        for t in group_threads:
            data.update({'threads[thread_fbids][{}]'.format(i): t})
            i += 1
        i = 0
        for t in user_threads:
            data.update({'threads[user_ids][{}]'.format(i): t})
            i += 1
        req = self.send_req('/ajax/mercury/thread_info.php', 1, data)
        check_for_messenger_error(req)
        return json.loads(req.text[9:])['payload']

    def get_users_info(self, users):
        data = {'fb_dtsg': self.dtsg_token, 'ttstamp': self.ttstamp}
        i = 0
        for t in users:
            data.update({'ids[{}]'.format(i): t})
            i += 1
        req = self.send_req('/chat/user_info/', 1, data)
        check_for_messenger_error(req)
        return json.loads(req.text[9:])['payload']

    def get_all_users_info(self):
        req = self.send_req('/chat/user_info_all/?viewer={}'.format(self.uid), 1, {'fb_dtsg': self.dtsg_token, 'ttstamp': self.ttstamp})
        check_for_messenger_error(req)
        return json.loads(req.text[9:])['payload']

    def search(self, query, existing_threads=(), limit=8):
        req = self.send_req('/ajax/mercury/composer_query.php', 0, {'value': query, 'limit': limit, 'existing_ids': ','.join(existing_threads)})
        check_for_messenger_error(req)
        return json.loads(req.text[9:])['payload']

    def set_mute_thread(self, thread, mutetime):
        data = {'thread_fbid': thread, 'mute_settings': mutetime,
                'fb_dtsg': self.dtsg_token, 'ttstamp': self.ttstamp}
        req = self.send_req('/ajax/mercury/change_mute_thread.php', 1, data)
        check_for_messenger_error(req)
        return req

    def pull(self):
        if self.partition is None or self.user_channel is None or self.pull_host is None or self.seq is None:
            raise NeedReconnect

        params = {'channel': self.user_channel, 'seq': self.seq, 'partition': self.partition, 'clientid': self.sessid,
                  'cb': str_base(random.randint(0, 1048575)), 'idle': 0, 'cap': 0, 'msgs_recv': self.seq,
                  'uid': self.uid, 'viewer_uid': self.uid, 'state': 'offline'}

        if self.sticky_token and self.sticky_pool:
            params.update({'sticky_token': self.sticky_token, 'sticky_pool': self.sticky_pool})

        if self.tr:
            params.update({'traceid': self.tr})

        resp = self.sess.get('https://{}.messenger.com/pull'.format(self.pull_host), params=params)
        data = json.loads(resp.text[9:])

        if 'seq' in data:
            self.seq = data['seq']

        if 'tr' in data:
            self.tr = data['tr']

        if data['t'] == 'lb':
            self.sticky_token = data['lb_info']['sticky']
            self.sticky_pool = data['lb_info']['pool']
        elif data['t'] == 'msg':
            return data['ms']

        return []

    def logout(self):
        self.sess.post('https://www.messenger.com/logout/', {'fb_dtsg': self.dtsg_token})
