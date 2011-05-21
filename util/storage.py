import urllib, os, time
try:
    import cPickle as pickle
except ImportError:
    import pickle
from logger import log

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

class PersistentCacher(object):
    def __init__(self, localdir="/tmp/lyrebird/", max_age_in_days=-1, verbose=False):
        self.verbose = verbose
        self.max_age_in_days = max_age_in_days
        self.localdir = os.path.realpath(os.path.dirname(localdir))
        if not os.path.isdir(localdir):
            os.mkdir(localdir)
        self.dloader = urllib.FancyURLopener()
        self.exp = -1
        self.dont_dl = (".swf",)
        self.storpath = storpath = os.path.join( self.localdir, "agedic.pkl" )
        self.stor = {}
        successful = False
        if os.path.exists( storpath ):
            try:
                self.stor = pickle.load( open(storpath, 'r'), -1 )
                successful = True
            except:
                log("Cache corrupted.. will try to rebuild it.")

    def check_for_old_files(self, max_age_in_days):
        # first search for really existing && unrotten files,
        # then burn the rest.
        existing = set([self.storpath])
        then = time.time() - max_age_in_days*24*60*60
        for url, (newurl,creation) in self.stor.items():
            if creation < then:
                self.__remove_item(url)
            else:
                existing.add(newurl)
        files = [os.path.join(self.localdir, f) for f in os.listdir(self.localdir)]
        for f in set(files).difference(existing):
            os.remove(os.path.join( self.localdir, f))

    def __newurl(self, url):
        return os.path.join(self.localdir, str(hex(hash(url))).replace("-","0"))

    def __getitem__(self, url):
        if url[-4:] in self.dont_dl:
            self.verbose and log("Ignoring "+ url)
            return url
        try:
            result, tt = self.stor[url]
            if not os.path.exists(result):
                raise KeyError()
            self.stor[url] = self.stor[self.stor[url]] = (self.stor[url][0], time.time())
            self.verbose and log("Getting %s from cache." % url)
            return result
        except KeyError:
            newurl = self.__newurl(url)
            self.verbose and log("Downloading %s." % url)
            try:
                if not os.path.exists(newurl):
                    self.dloader.retrieve(url, newurl)
                self.verbose and log("Cached %s to %s." % (url, newurl, ))
                self.stor[url] = self.stor[newurl] = (newurl, time.time())
            except IOError:
                self.verbose and log("IOError: Filename too long?") 
            return newurl

    def __remove_item(self, url):
        try:
            os.remove(self.stor[url])
            del self.stor[self.__newurl(url)]
            del self.stor[url]
        except:
            pass # oll korrect

    def __delitem__(self, url):
        self.__remove_item(url)

    def pprint(self):
        try:
            import pprint as p
            p.pprint(self.stor, indent=2, width=50)
        except ImportError:
            print(self.stor)

    def quit(self):
        done = False
        while not done:
            try:
                pickle.dump(self.stor, open(self.storpath, 'w'), -1)
                done = True
            except RuntimeError:
                pass
        self.check_for_old_files(self.max_age_in_days)

    def clear():
        for url in self.stor.values():
            os.remove(url) # uh oh
        self.stor = {}

if __name__ == "__main__":
    c = Cacher()
    print c["abc"]
    c["abc"] = 1
    print c["abc"]
