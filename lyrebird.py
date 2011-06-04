#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import feedparser, sys, os, urllib, argparse
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
NUMT = 8
__appname__ = "Lyrebird"
__version__ = "0.1 Coccatoo"
__author__ = "spazzpp2"

class lyrebird( object ):
    def __init__( self, nogui=False, verbose=False, cache_only=False ):
        self.verbose = verbose

        self.__prepare() # calls exit(1) if instance creation is locked
        self.__setup_dl_pipes()

        # echo cache
        if cache_only:
            # kill all threads
            self.dl_running = False
            # print
            self.cache.pprint()
            # quit
            self.cache.quit()
            self.config.quit()
            sys.exit(0)

    def __prepare( self ):
        # load config
        try:
            self.config = Config( HOME, verbose=self.verbose ) # Raises Exception if locked
        except:
            log(_( "It seems as if Lyrebird is already running. If not, please remove ~/.lyrebird/lock" ))
            sys.exit( 1 )

        # prepare cached browser
        self.browser = browser.WebkitBrowser( HERE )
        self.browser.set_about_handler( self.__about )
        self.cache = storage.PersistentCacher( TEMP, 3 , self.verbose) # keeps files for 3 days

        # prepare variables and lists,...
        self.feeds = {}
        self.watched = None
        self.mblog = Microblogger()
        self.crawler = Crawler( self.cache )
        self.crawler.verbose = self.verbose
        self.window = main_window( {
                "__appname__": __appname__,
                "__version__": __version__,
                "__author__":  __author__,
            }, self )

    def __setup_dl_pipes( self ):
        # setup download pipes
        self.dl_queue = Queue.Queue()
        self.dl_running = True
        for i in range( NUMT ):
            t = threading.Thread( target=self.__dl_worker, args=( False, self.update_feeds_tree,  ) )
            t.daemon = True
            t.start()

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
                    if self.verbose:
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
            if self.verbose:
                log( "Couldn't find feed[feed][title] in %s" % url )
        if url in self.window.treedic.keys():
            self.window.groups.get_model().set( self.window.treedic[url], 0, title, 1, url )
        else:
            self.window.treedic[url] = self.window.groups.get_model().append( self.window.treedic["Feeds"], [title, url] )
        self.window.groups.expand_all()
        gtk.gdk.threads_leave()

    def quit( self, stuff=None ):
        # stop downloading
        self.dl_running = False
        # quit
        self.cache.quit()
        self.config.quit()
        gtk.main_quit()

    def __dl_worker( self, cached=False, callback=None ):
        while self.dl_running:
            url = self.dl_queue.get()
            self.download( url, cached, callback )
            self.dl_queue.task_done()

    def download( self, feedurl, cached=True, callback=None ):
        if not cached:
            self.feeds[feedurl] = feedparser.parse( feedurl )
        else:
            self.feeds[feedurl] = feedparser.parse( self.cache[feedurl] )
        self.feeds[feedurl] = self.crawler.enrich(self.feeds[feedurl])
        if self.verbose:
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
                self.dl_queue.put_nowait( url )
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

def main( urls=[], nogui=False, cache_only=False, verbose=False ):
    gobject.threads_init()
    l = lyrebird(nogui, verbose, cache_only)
    gobject.idle_add( l.show )
    for url in urls:
        gobject.idle_add( l.add_url, ( url, ) )
    gtk.main()

def get_cmd_options():
    usage = "lyrebird.py"

if __name__ == "__main__":
    if len( sys.argv ) > 1:
        if len(sys.argv) > 1:
            main(   sys.argv[1:] if "-a" in sys.argv else [],
                    "-n" in sys.argv,
                    "-c" in sys.argv,
                    "-v" in sys.argv )
    else:
        main()
