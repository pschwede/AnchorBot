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
    def __init__(self, localdir="/tmp/lyrebird/"):
        self.stor = {}
        self.localdir = os.path.realpath(os.path.dirname(localdir))
        if not os.path.isdir(localdir):
            log("%s did not exist until now." % localdir)
            os.mkdir(localdir)
        self.dloader = urllib.FancyURLopener()
        self.exp = -1
        self.donotdl = (".swf")

    def __getitem__(self, url, verbose=False):
        if url[-4:] in self.donotdl:
            if verbose:
                log("ignoring "+ url)
            return url
        try:
            res = self.stor[url]
            if verbose:
                log("Getting %s from cache." % url)
            return res
        except KeyError:
            newurl = os.path.join(self.localdir, str(hash(url)).replace("-","0"))
            ending = os.path.splitext(url)[-1]
            if ending:
                newurl += ending
            else:
                newurl += ".xml"
            self.stor[url] = newurl
            self.stor[newurl] = newurl
            if os.path.exists(newurl):
                #TODO check for expiration date ;)
                if verbose:
                    log("Using old cached %s for %s." % (newurl, url, ))
                return newurl
            else:
                log("Downloading %s." % url)
                self.dloader.retrieve(url, newurl) #TODO make it threaded
                if verbose:
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
