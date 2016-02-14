from datetime import datetime
from base.MessengerAPI import MessengerAPI
from base.MessengerPullParserV2 import MessengerPullParser
from base.Exceptions import UserNotFoundException, UnknownThreadException, UnknownPersonException, MessengerException
from Person import Person
from Thread import Thread, PrivateThread

__author__  = 'JuniorJPDJ'
__version__ = 0.1

# TODO: Make use of PullParser


class Messenger(object):
    def __init__(self, login, pw, useragent='default'):
        self.msgapi = MessengerAPI(login, pw, useragent)
        self._pparser = MessengerPullParser(self.msgapi)
        self._people = {}
        self._threads = {}
        self._threadlist_offset = 0
        self.ordered_thread_list = []
        self.parse_threadlist(self.msgapi.mercury_payload)
        self.me = self.get_person(int(self.msgapi.uid))

    def parse_threadlist(self, threadlist):
        # TODO: load thread read/delivery time (read = roger, delivery = delivery_receipts)
        if 'participants' in threadlist:
            for p in threadlist['participants']:
                if p['fbid'] not in self._people:
                    self._people[p['fbid']] = Person.from_dict(self, p)
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
                        self.ordered_thread_list.append(int(th['thread_fbid']))
                    break
        return new_threads

    def get_person_from_cache(self, fbid):
        if fbid in self._people:
            return self._people[fbid]
        else:
            raise UnknownPersonException

    def get_person(self, fbid):
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
        if fbid in self._threads:
            return self._threads[fbid]
        else:
            raise UnknownThreadException

    def get_thread(self, fbid):
        # Pls don't kill me
        try:
            return self.get_thread_from_cache(fbid)
        except UnknownThreadException:
            try:
                self.get_person(fbid)
                data = self.msgapi.get_threads_info((), (fbid,))
                if 'threads' in data and len(data['threads']):
                    thread = Thread.from_dict(self, data['threads'][0])
                else:
                    thread = PrivateThread(self, fbid, True, False, 'inbox', None, None, None, 0, 0, datetime.now(), datetime.now())
                self._threads[fbid] = thread
                return thread
            except UserNotFoundException:
                try:
                    data = self.msgapi.get_threads_info((fbid,))
                    if 'threads' not in data or not len(data['threads']):
                        raise UnknownThreadException
                    thread = Thread.from_dict(self, data['threads'][0])
                    self._threads[fbid] = thread
                    return thread
                except MessengerException:
                    raise UnknownThreadException

    def load_more_threads(self, amount=10):
        return self.parse_threadlist(self.msgapi.get_thread_list(limit=amount, offset=self._threadlist_offset))

    def load_people_from_friends(self):
        # TODO: get_all_users_info
        raise NotImplementedError

    def search(self, query, amount=8):
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

    def logout(self):
        self.msgapi.logout()
