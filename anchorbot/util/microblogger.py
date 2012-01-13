try:
    import tweepy
    TWEEPY = True
except ImportError:
    print _("No Tweepy installed? Please run 'sudo easy_install tweepy'!")
    TWEEPY = False

class Microblogger( object ):
    def __init__( self, name, passwd, host="identi.ca/api"):
        self.__name_passwd = (name, passwd)
        self.host = host

    def send_text( self, text, url):
        if TWEEPY: # if installed
            uri = self.host.split( "/" )
            self.auth = tweepy.BasicAuthHandler( *self.__name_passwd )
            if len( uri ) > 1:
                api_root = "/" + "/".join( uri[1:] )
                self.client = tweepy.API( self.auth, uri[0], api_root=api_root, secure=True )
            else:
                self.client = tweepy.API( self.auth, uri[0], secure=True )
            self.client.update_status( u"" + text )

if __name__ == "__main__":
    mb = Microblogger()
    mb.send_text( "Testing #Tweepy" )
