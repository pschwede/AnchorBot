import urllib, os
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
    def __init__(self, localdir="/tmp/"):
        self.stor = {}
        self.localdir = os.path.realpath(os.path.dirname(localdir))
        self.dloader = urllib.FancyURLopener()
        self.exp = -1

    def __getitem__(self, url):
        try:
            res = self.stor[url]
            log("Getting %s from cache." % url)
            return res
        except KeyError:
            newurl = os.path.join(self.localdir, str(hash(url)).replace("-","0")+".xml")
            self.stor[url] = newurl
            if os.path.exists(newurl):
                #TODO check for expiration date ;)
                log("Using old cached %s for %s." % (newurl, url, ))
                return newurl
            else:
                print self.dloader.retrieve(url, newurl)
                log("Cached %s to %s." % (url, newurl, ))
                return newurl

    def __delitem__(self, url):
        try:
            os.remove(self.stor[url])
            del self.stor[url]
        except:
            pass # oll korrect

    def clear():
        for url in self.stor.values():
            os.remove(url) # uh oh
        self.stor = {}

if __name__ == "__main__":
    c = Cacher()
    print c["abc"]
    c["abc"] = 1
    print c["abc"]
