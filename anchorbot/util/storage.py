import urllib
import os
import time
try:
    import cPickle as pickle
except ImportError:
    import pickle
from logger import log #TODO use Logger here
from threading import Thread
from Queue import Queue
from StringIO import StringIO

class Cacher(object):
    """
    Object-Wrapper around a dict. Have seen smaller and quickier, though.
    """
    def __init__(self):
        self.dic = {}

    def get(self, url):
        return self.dic[url]

    def __getitem__(self, url):
        try:
            obj = self.dic[url]
            log("Ha! Gottcha!")
            return obj
        except KeyError:
            return None

    def __setitem__(self, url, obj):
        if self[url]:
            log("Overwriting %s" % url)
        self.dic[url] = obj

    def clear(self):
        self.dic = {}

class NotCachingError(Exception):
    def __init__(self, msg):
        Exception.__init__(self, msg)

class FileCacher(dict):
    def __init__(self, localdir="/tmp/lyrebird/", max_age_in_days= -1, verbose=False, dont_dl=[], dlnum=8):
        if not dont_dl:
            dont_dl = [".gif",".swf",".iso",".zip",".avi",".mp3",".ogg"]
        self.verbose = verbose
        self.max_age_in_days = max_age_in_days
        self.localdir = os.path.realpath(os.path.dirname(localdir))
        if not os.path.exists(localdir):
            os.mkdir(localdir)
        self.exp = -1
        self.dont_dl = dont_dl
        self.url_last_used_path = url_last_used_path = os.path.join(self.localdir, "agedic.pkl")
        self.url_last_used = {}

        self.dloader = urllib.FancyURLopener()
        self.dlqueue = Queue()
        
        if os.path.exists(url_last_used_path):
            try:
                self.url_last_used = pickle.load(open(url_last_used_path, 'r'), -1)
            except:
                pass

        self.vacuum(self.max_age_in_days)

    def vacuum(self, max_age_in_days):
        # first search for really existing && unrotten files,
        # then burn the rest.
        then = time.time() - max_age_in_days * 24 * 60 * 60
        for root, dirs, files in os.walk(self.localdir):
            for path in [os.path.join(self.localdir, f) for f in files]:
                try:
                    if os.stat(path).st_atime < then:
                        print "cleaning %s" % path
                        os.remove(path)
                except OSError:
                    pass

    def __newurl(self, url):
        return os.path.join(self.localdir, str(hex(hash(url))).replace("-", "0"))

    def __retrieve(self, url, newurl):
        tries = 4
        done = False
        while tries and not done:
            tries-=1
            try:
                self.dloader.retrieve(url, newurl)
                done = True
            except IOError, e:
                log("IOError during retrieving %s" % url)
    
    def __queued_retrieve(self):
        while not self.dlqueue.empty():
            self.__getitem__(self.dlqueue.get())
            self.dlqueue.task_done()

    def chunk(self, url):
        """Returns only the first 512 Bytes. Can be used to get image size with PIL"""
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
        for i in range(min(10, len(urls))):
            t = Thread(target=self.__queued_retrieve)
            t.start()
        self.dlqueue.join()
        return [self.__getitem__(url) for url in valid_urls]

    def __getitem__(self, url):
        if not url:
            return None
        if url == u"None":
            return None
        if isinstance(url, unicode):
            url = (url.encode("utf-8"))
        if url[-4:] in self.dont_dl:
            raise Exception("Not downloading %s" % url)
        try:
            result = self.url_last_used[url][0]
            if not os.path.exists(result):
                raise KeyError()
            self.url_last_used[url] = self.url_last_used[self.url_last_used[url]] = (self.url_last_used[url][0], time.time())
            #self.verbose and log("Getting %s from cache." % url)
            return result
        except KeyError:
            newurl = self.__newurl(url)
            try:
                if not os.path.exists(newurl):
                    self.__retrieve(url, newurl)
                    #self.verbose and log("Cached %s to %s." % (url, newurl,))
                self.url_last_used[url] = self.url_last_used[newurl] = (newurl, time.time())
            except IOError, e:
                self.verbose and log("IOError during download of %s" % url)
                return url
            return newurl

    def __delitem__(self, url):
        try:
            try:
                os.remove(self.url_last_used[url][0])
            except OSError,e:
                if e.errno == 2:
                    pass
                else:
                    print e.message
            del self.url_last_used[url]
            del self.url_last_used[self.__newurl(url)]
        except KeyError:
            pass # Oll Korrect

    def pprint(self):
        try:
            import pprint as p
            p.pprint(self.url_last_used, indent=2, width=50)
        except ImportError:
            print(self.url_last_used)

    def shutdown(self):
        done = False
        while not done:
            try:
                pickle.dump(self.url_last_used, open(self.url_last_used_path, 'w'), -1)
                done = True
            except RuntimeError:
                pass
        #self.dloader.urlcleanup()

    def clear(self):
        for url in self.url_last_used.values():
            os.remove(url)
        self.url_last_used = {}

if __name__ == "__main__":
    c = Cacher()
    print c["abc"]
    c["abc"] = 1
    print c["abc"]
