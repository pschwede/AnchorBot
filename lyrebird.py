#!/usr/bin/env python
# -*- encoding: utf-8 -*-

"""
This is the main file of Lyrebird, the feed reader that makes you read 
the important news first.

For further reading, see README.md
"""

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
    """ The most main Class

    It holds and calls initialization of:
    * singleton instance lock
    * main window
    * configurations
    * feed downloads
    * start analysis of the downloaded feeds
    """

    def __init__( self, nogui=False, verbose=False, cache_only=False ):
        self.verbose = verbose

        # prepare lock, config, cache and variables
        try:
            self.__prepare()
        except IOError:
            sys.exit( 1 )
        self.__setup_dl_pipes( NUMT )

        # print out cache and exit
        if cache_only:
            self.__print_cache_and_exit()

    def __prepare( self ):
        """ Checks lock, reads config, initializes cache, etc.
        
        Raises IOError-exception if Lyrebird is already running.
        """

        # load config
        try:
            self.config = Config( HOME, verbose=self.verbose ) # Raises Exception if locked
        except:
            log(_( "It seems as if Lyrebird is already running. If not, please remove ~/.lyrebird/lock" ))
            raise IOError()

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

    def __setup_dl_pipes( self, number_of_pipes ):
        """ initializes a list of Download Threads and a Queue.Queue """
        # setup download pipes
        self.dl_queue = Queue.Queue()
        self.dl_running = True
        for i in range( number_of_pipes ):
            t = threading.Thread( target=self.__dl_worker, args=( False, self.update_feeds_tree,  ) )
            t.daemon = True
            t.start()

    def __print_cache_and_exit( self ):
        """ well, prints cache and exits """
        # kill all threads
        self.dl_running = False
        # print
        self.cache.pprint()
        # quit
        self.cache.quit()
        self.config.quit()
        sys.exit(0)

    def __about( self, uri ):
        """handles "about:"-url-requests.
        """
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
        """Opens single feeds or combined (grouped) ones in browser.
        """
        self.browser.openfeed( url )

    def update_feeds_tree( self, url ):
        """Redraws the Feed-Tree
        """
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
        """Does a save Quit
        """
        # stop downloading
        self.dl_running = False
        # quit
        self.cache.quit()
        self.config.quit()
        gtk.main_quit()

    def __dl_worker( self, cached=False, callback=None ):
        """Method for Download Threads
        
        Setting self.dl_running to False would stop them all.
        """
        while self.dl_running:
            url = self.dl_queue.get()
            self.download( url, cached, callback )
            self.dl_queue.task_done()

    def download( self, feedurl, cached=True, callback=None ):
        """Download procedure
        """
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
        """Puts all feeds into the download queue to be downloaded.
        """
        for url in self.config.get_abos():
            self.dl_queue.put_nowait( url )

    def show( self, url=None ):
        """Shows url in browser. If url is already shown in browser,
        the feed will be downloaded again.
        """
        if not url and self.watched:
            url = self.watched
        if url:
            if url == self.watched:
                self.dl_queue.put_nowait( url )
            self.browser.openfeed( self.feeds[url] )
        else:
            self.download_all( self.update_feeds_tree )
        self.watched = url

    def add_url( self, url ):
        """Adds a feed url to the abos
        """
        self.config.add_abo( url )
        self.download( url )
        self.show( url )
        self.update_feeds_tree( url )

    def remove_url( self, url ):
        """Removes a feed url from the abos
        """
        self.config.del_abo( url )
        self.update_feeds_tree( url )

def main( urls=[], nogui=False, cache_only=False, verbose=False ):
    """The main func which creates Lyrebird
    """
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
                    "-n" in sys.argv, # no-gui option
                    "-v" in sys.argv, # verbose option
                    "-c" in sys.argv )# print cache only
    else:
        main()
