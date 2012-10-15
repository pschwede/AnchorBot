import urllib
import os
import time
import pprint
import logging
try:
    import cPickle as pickle
except ImportError:
    import pickle
from threading import Thread
from Queue import Queue
from StringIO import StringIO


class LimitedDict(dict):
    def __init__(self, size=5, **kwargs):
        self.maxsize = size
        self.accesses = 0
        self.update(kwargs)
        self.logger = logging.getLogger("root")

    def find_least_accessed_key(self):
        delme = None
        items = self.items()
        if items:
            delme = items[0][0]  # default is the key of oldest item in items list
            val = self.accesses  # biggest possible number
            for key, obj in self.items():
                if obj[0] < val: delme = key
        return delme

    def __setitem__(self, key, obj):
        if super(LimitedDict, self).__contains__(key):  
            self.logger.debug("just overwriting")
            super(LimitedDict, self).__setitem__(key, (0, obj))
            return

        if len(self) >= self.maxsize:
            delme = self.find_least_accessed_key()
            self.logger.debug("deleting %s" % delme)
            if delme:
                super(LimitedDict, self).__delitem__(delme)

        self.logger.debug("adding %s" % str((key, (0, obj))))
        super(LimitedDict, self).__setitem__(key, (0, obj))

    def __getitem__(self, key):
        if key in self.keys():
            # inc item access count
            item = super(LimitedDict, self).__getitem__(key)  # should not raise KeyError
            item = (item[0]+1, item[1])
            super(LimitedDict, self).__setitem__(key, item)

            # inc global access count
            self.accesses += 1
            return item[1]

class FileCacher(dict):
    def __init__(self,
            localdir="/tmp/lyrebird/",
            max_age_in_days=-1,
            dont_dl=[],
            dlnum=8,
            memory=30):
        if not dont_dl:
            dont_dl = ["r.xz", ".jar", ".gif", ".swf", ".iso", ".zip", ".avi", ".mp3", ".ogg"]
        self.dlnum = dlnum
        self.max_age_in_days = max_age_in_days
        self.localdir = os.path.realpath(os.path.dirname(localdir))
        if not os.path.exists(localdir):
            os.mkdir(localdir)
        self.exp = -1
        self.dont_dl = dont_dl
        self.url_last_used_path = url_last_used_path = os.path.join(
                self.localdir, "agedic.pkl")
        self.url_last_used = {}
        self.logger = logging.getLogger("root")

        self.dloader = urllib.FancyURLopener()
        self.dlqueue = Queue()
        self.dlthreads = list()

        self.running = True

        if os.path.exists(url_last_used_path):
            try:
                self.url_last_used = pickle.load(
                        open(url_last_used_path, 'r'),
                        -1)
            except:
                pass

    def vacuum(self, max_age_in_days):
        # first search for really existing && unrotten files,
        # then burn the rest.
        then = time.time() - max_age_in_days * 24 * 60 * 60
        for root, dirs, files in os.walk(self.localdir):
            for path in [os.path.join(self.localdir, f) for f in files]:
                try:
                    if os.stat(path).st_atime < then:
                        self.logger.debug("Removing %s" % path)
                        os.remove(path)
                except OSError:
                    pass

    def __newurl(self, url):
        return os.path.join(self.localdir, str(hex(hash(url))).replace("-","0"))

    def __retrieve(self, url, newurl, tries=4):
        self.logger.debug("[  DL  ] %s" % url)
        if tries > 0:
            try:
                self.dloader.retrieve(url, newurl)
            except Exception, e:
                self.__retrieve(url, newurl, tries-1)

    def __queued_retrieve(self):
        while not self.dlqueue.empty():
            item = self.dlqueue.get(1000)
            self.__getitem__(item)
            self.dlqueue.task_done()

    def chunk(self, url):
        """
        Returns only the first 512 Bytes. Can be used to get image size
        with PIL
        """
        if url[-4:] in self.dont_dl:
            raise Exception("Not downloading %s" % url)
        f = urllib.urlopen(url)
        s = StringIO(f.read(512))
        return s

    def get_all(self, urls, delete=False):
        if delete:
            for url in urls:
                self.__delitem__(url)
        valid_urls = []
        for url in urls:
            if url[-4:] not in self.dont_dl:
                self.dlqueue.put(url)
                valid_urls.append(url)
        self.logger.debug("Downloading %i urls." % len(valid_urls))
        for i in range(self.dlnum):
            t = Thread(target=self.__queued_retrieve)
            t.daemon = True
            t.start()
        self.dlqueue.join()
        return [self.__getitem__(url) for url in valid_urls]

    def __getitem__(self, url):
        if not url:
            return None
        if isinstance(url, unicode):
            url = url.encode("utf-8")
        if url[-4:] in self.dont_dl:
            raise Exception("Not downloading %s" % url)
        try:
            result = self.url_last_used[url][0]
            if not os.path.exists(result):
                raise KeyError()
            self.url_last_used[url] = self.url_last_used[
                        self.url_last_used[url]
                    ] = (self.url_last_used[url][0], time.time())
            #self.logger.debug("Getting %s from cache." % url)
            return result
        except KeyError:
            newurl = self.__newurl(url)
            try:
                if not os.path.exists(newurl):
                    self.__retrieve(url, newurl)
                    #self.logger.debug("Cached %s to %s." % (url, newurl,))
                self.url_last_used[url] = self.url_last_used[newurl] = (
                        newurl,
                        time.time())
            except IOError, e:
                self.logger.error("IOError during download of %s" % url)
                return url
            return newurl

    def __delitem__(self, url):
        try:
            try:
                os.remove(self.url_last_used[url][0])
            except OSError, e:
                if e.errno == 2:
                    pass
                else:
                    self.logger.error(e.message)
            del self.url_last_used[url]
            del self.url_last_used[self.__newurl(url)]
        except KeyError:
            pass  # Oll Korrect

    def pprint(self):
        try:
            pprint.pprint(self.url_last_used, indent=2, width=50)
        except ImportError:
            self.logger.info(self.url_last_used)

    def shutdown(self):
        done = False
        self.running = False
        self.vacuum(self.max_age_in_days)
        while not done:
            try:
                pickle.dump(
                        self.url_last_used,
                        open(self.url_last_used_path, 'w'),
                        -1)
                done = True
            except RuntimeError:
                pass
        #self.dloader.urlcleanup()

    def clear(self):
        for url in self.url_last_used.values():
            os.remove(url)
        self.url_last_used = {}


if __name__ == "__main__":
    d = LimitedDict()
    for i in range(5):
        d[i] = i
    print d, d.accesses
    print d[0], d[1], d[2], d[3]
    print d, d.accesses
    d[99] = 99
    print d, d.accesses
