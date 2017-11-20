from __future__ import unicode_literals

from datetime import datetime
from collections import defaultdict

from .base.Exceptions import UserNotFoundException, UnknownThreadException, UnknownPersonException, MessengerException
from .MessengerPullParser import MessengerPullParser
from .DefaultActionHandlers import register_handlers
from .base.MessengerAPI import MessengerAPI
from .Thread import Thread, PrivateThread
from .Attachments import AttachmentUploader
from .Person import Person
from .utils.universal_type_checking import is_integer

__author__ = 'JuniorJPDJ'
__version__ = 0.1


class Messenger(object):
    def __init__(self, login, pw, timezone=None, useragent='default'):
        self.msgapi = MessengerAPI(login, pw, timezone, useragent)
        self._uploader = AttachmentUploader(self)
        self._pparser = MessengerPullParser(self)
        self._people = {}
        self._threads = {}
        self._threadlist_offset = 0
        self.ordered_thread_list = []
        self.__action_handlers = defaultdict(lambda: [])
        self.me = self.get_person(int(self.msgapi.uid))
        self._pparser.register_actions_handler(self._handle_action)
        self._parse_threadlist(self.msgapi.mercury_payload)
        register_handlers(self)
        for p in self.msgapi.last_active.items():
            self.get_person(int(p[0])).last_active = datetime.fromtimestamp(p[1])

    def _parse_threadlist(self, threadlist):
        if 'participants' in threadlist:
            for p in threadlist['participants']:
                if p['fbid'] not in self._people:
                    self._people[int(p['fbid'])] = Person.from_dict(self, p)
        new_threads = {}
        if 'threads' in threadlist:
            for t in threadlist['threads']:
                if int(t['thread_fbid']) not in self._threads:
                    self._threadlist_offset += 1
                    new_threads[int(t['thread_fbid'])] = Thread.from_dict(self, t)
        self._threads.update(new_threads)
        for t in threadlist['ordered_threadlists'][0]['thread_ids']:
            for th in threadlist['threads']:
                if t == th['thread_id']:
                    if int(th['thread_fbid']) not in self.ordered_thread_list:
                        self.ordered_thread_list.append(self.get_thread(int(th['thread_fbid'])))
                    break
        if 'delivery_receipts' in threadlist:
            for t in threadlist['delivery_receipts']:
                self.get_thread(int(t['thread_fbid'] if t['thread_fbid'] is not None else t['other_user_fbid'])).last_delivery = datetime.fromtimestamp(t['time'] / 1000.0)
        if 'roger' in threadlist and isinstance(threadlist['roger'], dict):
            for t in threadlist['roger'].items():
                th = self.get_thread(int(t[0]))
                for p in t[1]:
                    th.last_read[self.get_person(int(p))] = datetime.fromtimestamp(t[1][p]['action'] / 1000.0)
        return new_threads

    def _handle_action(self, action):
        for handler in self.__action_handlers[action.__class__]:
            handler(action)

    def get_person_from_cache(self, fbid):
        '''
        :return: Person
        '''
        if fbid in self._people:
            return self._people[fbid]
        else:
            raise UnknownPersonException

    def get_person(self, fbid):
        '''
        :return: Person
        '''
        assert is_integer(fbid)
        try:
            return self.get_person_from_cache(fbid)
        except UnknownPersonException:
            data = self.msgapi.get_users_info((fbid,))['profiles']
            if str(fbid) not in data:
                raise UserNotFoundException
            p = Person.from_dict(self, data[str(fbid)])
            self._people[fbid] = p
            return p

    def get_thread_from_cache(self, fbid):
        '''
        :return: Thread
        '''
        if fbid in self._threads:
            return self._threads[fbid]
        else:
            raise UnknownThreadException

    def get_thread(self, fbid):
        '''
        :return: Thread
        '''
        assert is_integer(fbid)
        # Pls don't kill me
        try:
            return self.get_thread_from_cache(fbid)
        except UnknownThreadException:
            try:
                self.get_person(fbid)
            except UserNotFoundException:
                try:
                    data = self.msgapi.get_threads_info((fbid,))
                except MessengerException:
                    raise UnknownThreadException
                else:
                    if 'threads' not in data or not data['threads']:
                        raise UnknownThreadException
                    thread = Thread.from_dict(self, data['threads'][0])
                    self._threads[fbid] = thread
                    return thread
            else:
                data = self.msgapi.get_threads_info((), (fbid,))
                if 'threads' in data and len(data['threads']):
                    thread = Thread.from_dict(self, data['threads'][0])
                else:
                    thread = PrivateThread(self, fbid, True, False, 'inbox', None, {}, None, 0, 0, datetime.now(),
                                           datetime.now(), False)
                self._threads[fbid] = thread
                return thread

    def load_more_threads(self, amount=10):
        '''
        :return: {int: Thread}
        '''
        return self._parse_threadlist(self.msgapi.get_thread_list(limit=amount, offset=self._threadlist_offset))

    def load_people_from_buddylist(self):
        # TODO: get_all_users_info
        raise NotImplementedError

    def search(self, query, amount=8):
        '''
        :return: {int: Thread}
        '''
        data = self.msgapi.search(query, limit=amount)
        threads = {}
        for e in data['entries']:
            if e['type'] == 'thread':
                try:
                    thread = self.get_thread(int(e['uid']))
                except UnknownThreadException:
                    thread = Thread.from_dict(self, e['mercury_thread'])
                threads[thread.fbid] = thread
            elif e['type'] == 'user':
                threads[int(e['uid'])] = self.get_person(int(e['uid'])).get_thread()
        self._threads.update(threads)
        return threads

# TODO: Implement priorities
    def register_action_handler(self, action, handler):
        self.__action_handlers[action].append(handler)

    def upload_attachment(self, filename, filelike, mimetype=None):
        '''
        :return: UploadedAttachment
        '''
        return self._uploader.upload(filename, filelike, mimetype)

    def pull(self):
        self._pparser.make_pull()

    def logout(self):
        self.msgapi.logout()
