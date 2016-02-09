import requests, json, time, random, logging

__author__ = 'JuniorJPDJ'

# DONE: add someone to thread
# DONE: kick someone from thread
# DONE: leave thread
# DONE: rename thread
# TODO: change thread image
# TODO: send typing status (stopped, started)
# TODO: send message read status
# TODO: show unread messages from time since program was not started
# TODO: change thread color theme
# TODO: change custom name of pariticipant of thread
# TODO: send last seen status


def str_base(num, b=36, numerals="0123456789abcdefghijklmnopqrstuvwxyz"):
    return ((num == 0) and numerals[0]) or (str_base(num // b, b, numerals).lstrip(numerals[0]) + numerals[num % b])


class NeedReconnectBeforePull(Exception):
    pass


class Messenger(object):
    def __init__(self, email, pw):
        self.sess = requests.Session()

        # self.sess.proxies.update({'https': 'https://127.0.0.1:8080'})
        # self.sess.verify = False
        # from requests.packages.urllib3.exceptions import InsecureRequestWarning
        # requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

        self.sess.headers.update(
            {'User-agent': 'Mozilla/5.0 ;compatible; FBMsgClient/0.1; KaziCiota; +http://juniorjpdj.cf;'})

        co = self.sess.get('https://www.messenger.com').content

        lsd_token = co.split('"token":"')[1].split('"')[0]
        initreqid = co.split('initialRequestID":"')[1].split('"')[0]
        timezone = (time.timezone if (time.localtime().tm_isdst == 0) else time.altzone) / 60
        lgnrnd = co.split('name="lgnrnd" value="')[1].split('"')[0]
        lgnjs = int(time.time())
        identifier = co.split('identifier":"')[1].split('"')[0]
        try:
            datr = co.split('"_js_datr","')[1].split('"')[0]
            self.sess.cookies.update({'_js_datr': datr})
        except IndexError:
            pass

        self.sess.get('https://www.facebook.com/login/messenger_dot_com_iframe/', params={'redirect_uri': 'https://www.messenger.com/login/fb_iframe_target/?initial_request_id={}'.format(
            initreqid), 'identifier': identifier, 'initial_request_id': initreqid})

        res = self.sess.post('https://www.messenger.com/login/password/',
                             {'lsd': lsd_token, 'initial_request_id': initreqid, 'timezone': timezone, 'lgnrnd': lgnrnd,
                              'lgnjs': lgnjs, 'email': email, 'pass': pw, 'default_persistent': 0}, headers={'Referer': 'https://www.messenger.com'})
        data = res.content

        self.dtsg_token = data.split('"token":"')[1].split('"')[0]

        self.ttstamp = '2'
        for w in range(len(self.dtsg_token)):
            self.ttstamp += str(ord(self.dtsg_token[w]))

        self.reqid = 0
        self.uploadid = 1023
        self.sessid = str_base(random.randint(0, 2147483647), 16)

        self.rev = data.split('revision":')[1].split(',')[0]
        self.uid = data.split('USER_ID":"')[1].split('"')[0]

        o = u''
        t = 0
        for c in data.split('"mercuryPayload":')[1]:
            if c == '{':
                t += 1
            elif c == "}":
                t -= 1
                if t == 0:
                    o += '}'
                    break
            o += c
        self.mercury_payload = json.loads(o)

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

    def send_msg(self, to, msg='', attachment=None, group=False):
        to = unicode(to)
        msg = unicode(msg)
        data = {'message_batch[0][action_type]': 'ma-type:user-generated-message',
                'message_batch[0][author]': 'fbid:' + self.uid, 'message_batch[0][source]': 'source:messenger:web',
                'message_batch[0][body]': msg, 'message_batch[0][has_attachment]': 'false', 'message_batch[0][html_body]': 'false', 'client': 'mercury',
                'fb_dtsg': self.dtsg_token, 'ttstamp': self.ttstamp}
        if group:
            userdata = {'message_batch[0][thread_fbid]': to}
        else:
            userdata = {'message_batch[0][specific_to_list][0]': 'fbid:' + to,
                        'message_batch[0][specific_to_list][1]': 'fbid:' + self.uid,
                        'message_batch[0][client_thread_id]': 'user:' + to}
        data.update(userdata)

        if attachment:
            data.update(attachment)

        return self.send_req('/ajax/mercury/send_messages.php', 1, data)

    def send_log_message(self, thread_id, log_message_type, additional_data):
        data = {'message_batch[0][action_type]': 'ma-type:log-message',
                'message_batch[0][author]': 'fbid:' + self.uid,
                'message_batch[0][source]': 'source:messenger:web',
                'message_batch[0][log_message_type]': log_message_type,
                'message_batch[0][thread_fbid]': thread_id,
                'message_batch[0][offline_threading_id]': random.randint(0, 999999999999999999),
                'client': 'messenger', 'fb_dtsg': self.dtsg_token, 'ttstamp': self.ttstamp}
        data.update(additional_data)

        return self.send_req('/ajax/mercury/send_messages.php', 1, data)

    def add_to_thread(self, thread_id, users):
        return self.send_log_message(thread_id, 'log:subscribe', dict([['message_batch[0][log_message_data][added_participants][{}]'.format(users.index(x)), 'fbid:{}'.format(x)] for x in users]))

    def kick_from_thread(self, thread_id, user):
        data = {'fb_dtsg': self.dtsg_token, 'ttstamp': self.ttstamp}

        return self.send_req('/chat/remove_participants/?uid={}&tid={}'.format(user, group_id), 1, data)

    def leave_thread(self, thread_id):
        return self.kick_from_thread(group_id, self.uid)

    def rename_thread(self, thread_id, name):
        return self.send_log_message(thread_id, 'log:thread-name', {'message_batch[0][log_message_data][name]': name})

    def send_reconnect(self, reason=6):
        resp = self.send_req('/ajax/presence/reconnect.php', 0, {'reason': reason, 'fb_dtsg': self.dtsg_token})
        data = json.loads(resp.content[9:])
        self.partition = data['payload']['partition']
        self.user_channel = data['payload']['user_channel']
        self.pull_host = '{}-{}'.format(random.randint(0, 7), data['payload']['host'])
        self.seq = data['payload']['seq']

        return resp

    def send_pull(self):
        if self.partition is None or self.user_channel is None or self.pull_host is None or self.seq is None:
            raise NeedReconnectBeforePull

        params = {'channel': self.user_channel, 'seq': self.seq, 'partition': self.partition, 'clientid': self.sessid,
                  'cb': str_base(random.randint(0, 1048575)), 'idle': 0, 'cap': 0, 'msgs_recv': self.seq,
                  'uid': self.uid, 'viewer_uid': self.uid, 'state': 'offline'}

        if self.sticky_token and self.sticky_pool:
            params.update({'sticky_token': self.sticky_token, 'sticky_pool': self.sticky_pool})

        if self.tr:
            params.update({'traceid': self.tr})

        resp = self.sess.get('https://{}.messenger.com/pull'.format(self.pull_host), params=params)
        data = json.loads(resp.content[9:])

        if 'seq' in data:
            self.seq = data['seq']

        if 'tr' in data:
            self.tr = data['tr']

        if data['t'] == 'lb':
            self.sticky_token = data['lb_info']['sticky']
            self.sticky_pool = data['lb_info']['pool']
        elif data['t'] == 'msg':
            return data['ms']

        return None

    def get_friends(self):
        resp = self.send_req('/chat/user_info_all/?viewer={}'.format(self.uid), 1, {'fb_dtsg': self.dtsg_token, 'ttstamp': self.ttstamp})
        return json.loads(resp.content[9:])['payload']
