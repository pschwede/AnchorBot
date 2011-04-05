#!/usr/bin/env python

import feedparser, sys, os, urllib
import gtk, gtk.gdk, gobject
import threading, webbrowser, Queue
from tempfile import gettempdir

from util import browser, analyzer, storage, _
from util.logger import log
from util.config import Config
from util.microblogging import Microblogger
from util.crawler import Crawler
from util.widgets import main_window

HOME = os.path.join( os.path.expanduser( "~" ),".lyrebird" )
HERE = os.path.realpath( os.path.dirname( __file__ ) )
#TEMP = os.path.join( os.path.realpath( gettempdir() ), "lyrebird/" )
TEMP = os.path.join( HOME, "cache/" )
HTML = os.path.join( HOME, "index.html" )
NUMT = 4 # Number of download pipes
__appname__ = "Lyrebird"
__version__ = "0.1 Coccatoo"
__author__ = "spazzpp2"

class lyrebird( object ):
    def __init__( self, nogui=False ):
        try:
            self.config = Config( HOME ) # Raises Exception if locked
        except:
            print _( "It seams as if Lyrebird is already running. If not, please remove ~/.lyrebird/lock" )
            sys.exit( 1 )

        self.dl_queue = Queue.Queue()
        for i in range( NUMT ):
            t = threading.Thread( target=self.__dl_worker, args=( False, self.update_feeds_tree,  ) )
            t.daemon = True
            t.start()

        self.browser = browser.WebkitBrowser( HERE )
        self.browser.set_about_handler( self.__about )
        self.cache = storage.PersistentCacher( TEMP )
        self.feeds = {}
        self.watched = None
        self.mblog = Microblogger()
        self.crawler = Crawler( self.cache )
        self.window = main_window( {
                "__appname__": __appname__,
                "__version__": __version__,
                "__author__":  __author__,
            }, self )

    def __about( self, uri ):
        if uri.startswith( "about:" ):
            cmd = uri[6:]
            if cmd is "about":
                self.show_about()
            elif cmd.startswith( "share?" ):
                url, text = None, None
                for arg in cmd[6:].split( "&" ):
                    if arg.startswith( "url=" ):
                        url = urllib.unquote( arg[4:] )
                    if arg.startswith( "text=" ):
                        text = urllib.unquote( arg[5:] )
                if text or url:
                    log( 'Tweet %s %s' % ( text, url,  ) )
                    self.mblog.send_text( "%s %s" % ( text, url,  ) )

    def show_group( self, url ):
        self.browser.openfeed( url )

    def update_feeds_tree( self, url ):
        # removes old entry with url and appends a new one
        gtk.gdk.threads_enter()
        feed = self.feeds[url]
        # find title or set title to url
        title = url
        try:
            title = feed["feed"]["title"]
        except KeyError:
            log( "Couldn't find feed[feed][title] in "+url )
        if url in self.window.treedic.keys():
            self.window.groups.get_model().set( self.window.treedic[url], 0, title, 1, url )
        else:
            self.window.treedic[url] = self.window.groups.get_model().append( self.window.treedic["Feeds"], [title, url] )
        self.window.groups.expand_all()
        gtk.gdk.threads_leave()

    def quit( self, stuff=None ):
        self.config.quit()
        gtk.main_quit()

    def __dl_worker( self, cached=False, callback=None ):
        while True:
            url = self.dl_queue.get()
            self.download( url, cached, callback )
            self.dl_queue.task_done()

    def download( self, feedurl, cached=True, callback=None ):
        if not cached:
            del self.cache[feedurl]
        self.feeds[feedurl] = feedparser.parse( self.cache[feedurl] )
        for entry in self.feeds[feedurl]["entries"]:
            entry = self.crawler.enrich( entry )
        log( "*** " + str( self.feeds.keys().index( feedurl ) ) + " of " + str( len( self.feeds ) ) )
        if callback:
            callback( feedurl )

    def download_all( self, callback=None ):
        for url in self.config.get_abos():
            self.dl_queue.put_nowait( url )

    def show( self, url=None ):
        if not url and self.watched:
            url = self.watched
        if url:
            if url == self.watched:
                self.download( url, False )
            self.browser.openfeed( self.feeds[url] )
        else:
            #TODO analyze first
            self.download_all( self.update_feeds_tree )
        self.watched = url

    def add_url( self, url ):
        self.config.add_abo( url )
        self.download( url )
        self.show( url )
        self.update_feeds_tree( url )

    def remove_url( self, url ):
        self.config.del_abo( url )
        self.update_feeds_tree( url )

def main( urls=[] ):
    gobject.threads_init()
    l = lyrebird()
    gobject.idle_add( l.show )
    for url in urls:
        gobject.idle_add( l.add_url, ( url, ) )
    gtk.main()

def get_cmd_options():
    usage = "lyrebird.py"

if __name__ == "__main__":
    if len( sys.argv ) > 1:
        main( sys.argv[1:] )
    else:
        main()
