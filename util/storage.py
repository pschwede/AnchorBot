import urllib, os

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
            print "Ha! Gottcha!"
            return obj
        except KeyError:
            return None

    def __setitem__(self, url, obj):
        if self[url]:
            print "WARNING: overwriting %s" % url
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
            return self.stor[url]
        except KeyError:
            newurl = os.path.join(self.localdir, str(hash(url)).replace("-","0")+".xml")
            if os.path.exists(newurl):
                return newurl #TODO check if expired
            print "Caching to %s!" % newurl
            self.dloader.retrieve(url, newurl)
            self.stor[url] = (newurl, 0)
            return newurl

    def clear():
        for url in self.stor.values():
            os.remove(url) # uh oh
        self.stor = {}

if __name__ == "__main__":
    c = Cacher()
    print c["abc"]
    c["abc"] = 1
    print c["abc"]
