try:
    import tweepy
    TWEEPY = True
except ImportError:
    print "No Tweepy installed? Please download Tweepy from http://joshthecoder.github.com/tweepy/ or run 'easy_install tweepy'!"
    TWEEPY = False

from logger import log
from widgets import tweet_window

class Microblogger(object):
    def __init__(self, hosts="identi.ca/api", keys=dict()):
        global TWEEPY
        self.__auth_keys = keys
        self.hosts = []
        if type(hosts) == list:
            self.hosts += hosts
        elif type(hosts) == str:
            self.hosts.append(hosts)

    def send_text(self, text):
        if TWEEPY:
            #TODO OAuth
            for host in self.hosts:
                adr = host.split("/")
                if host in self.__auth_keys:
                    tw = tweet_window(adr[0], *self.__auth_keys, text=text)
                else:
                    tw = tweet_window(adr[0], text=text)
                npt = self.__auth_keys[host] = tw.run()
                if npt: #tuple of name, password and text
                    self.auth = tweepy.BasicAuthHandler(npt[0], npt[1])
                    if len(adr)>1:
                        api_root = "/"+"/".join(adr[1:])
                        self.client = tweepy.API(self.auth, adr[0], api_root=api_root, secure=True)
                    else:
                        self.client = tweepy.API(self.auth, adr[0], secure=True)
                    self.client.update_status(u""+npt[2])

if __name__ == "__main__":
    mb = Microblogger()
    mb.send_text("Testing #Tweepy")
